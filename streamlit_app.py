import os
import openai
import streamlit as st
import re
from openai import AssistantEventHandler
from typing_extensions import override

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Verify that all required secrets are loaded
required_secrets = [
    "ASSISTANT1_ID", "ASSISTANT2_ID", "ASSISTANT3_ID", "ASSISTANT4_ID"
]

missing_secrets = [secret for secret in required_secrets if secret not in st.secrets]

if missing_secrets:
    st.error(f"Missing required secrets: {', '.join(missing_secrets)}")
    st.stop()

assistants = {
    "assistant_1": "Assistant 1",
    "assistant_2": "Assistant 2",
    "assistant_3": "Assistant 3",
    "assistant_4": "Assistant 4"
}

assistant_ids = {
    "assistant_1": st.secrets["ASSISTANT1_ID"],
    "assistant_2": st.secrets["ASSISTANT2_ID"],
    "assistant_3": st.secrets["ASSISTANT3_ID"],
    "assistant_4": st.secrets["ASSISTANT4_ID"]
}

class EventHandler(AssistantEventHandler):
    @override
    def on_event(self, event):
        pass

    @override
    def on_text_created(self, text):
        st.session_state.current_message = ""
        with st.chat_message("Assistant"):
            st.session_state.current_markdown = st.empty()

    @override
    def on_text_delta(self, delta, snapshot):
        if snapshot.value:
            st.session_state.current_message = snapshot.value
            st.session_state.current_markdown.markdown(st.session_state.current_message, True)

    @override
    def on_text_done(self, text):
        clean_text = re.sub(r'【[^】]+】', '', text)
        st.session_state.current_markdown.markdown(clean_text, True)
        st.session_state.chat_log.append({"name": "assistant", "msg": clean_text})

    @override
    def on_tool_call_created(self, tool_call):
        st.session_state.current_tool_input = ""
        with st.chat_message("Assistant"):
            st.session_state.current_tool_input_markdown = st.empty()

    @override
    def on_tool_call_delta(self, delta, snapshot):
        if 'current_tool_input_markdown' not in st.session_state:
            with st.chat_message("Assistant"):
                st.session_state.current_tool_input_markdown = st.empty()

        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                st.session_state.current_tool_input += delta.code_interpreter.input
                input_code = f"### code interpreter\ninput:\n```python\n{st.session_state.current_tool_input}\n```"
                st.session_state.current_tool_input_markdown.markdown(input_code, True)

            if delta.code_interpreter.outputs:
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        pass

    @override
    def on_tool_call_done(self, tool_call):
        st.session_state.tool_calls.append(tool_call)
        if tool_call.type == "code_interpreter":
            input_code = f"### code interpreter\ninput:\n```python\n{tool_call.code_interpreter.input}\n```"
            st.session_state.current_tool_input_markdown.markdown(input_code, True)
            st.session_state.chat_log.append({"name": "assistant", "msg": input_code})
            st.session_state.current_tool_input_markdown = None
            for output in tool_call.code_interpreter.outputs:
                if output.type == "logs":
                    output = f"### code interpreter\noutput:\n```\n{output.logs}\n```"
                    with st.chat_message("Assistant"):
                        st.markdown(output, True)
                        st.session_state.chat_log.append({"name": "assistant", "msg": output})

def run_stream(user_input, assistant_id):
    if "thread" not in st.session_state:
        st.session_state.thread = openai.beta.threads.create()
        create_message(st.session_state.thread, user_input)
    create_message(st.session_state.thread, user_input)
    with openai.beta.threads.runs.stream(
        thread_id=st.session_state.thread.id,
        assistant_id=assistant_id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

def handle_uploaded_file(uploaded_file):
    file = openai.files.create(file=uploaded_file, purpose="assistants")
    return file

def render_chat():
    for chat in st.session_state.chat_log:
        with st.chat_message(chat["name"]):
            st.markdown(chat["msg"], True)

if "tool_calls" not in st.session_state:
    st.session_state.tool_calls = []

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "in_progress" not in st.session_state:
    st.session_state.in_progress = False

def disable_form():
    st.session_state.in_progress = True

def main():
    st.title("AI Assistant Chat")
    st.write("Ask questions about your dataset")
    assistant_selection = st.selectbox(
        "Choose an assistant",
        list(assistants.keys()),
        format_func=lambda x: assistants[x]
    )
    assistant_id = assistant_ids[assistant_selection]

    st.sidebar.title("Assistant Selector")
    st.sidebar.selectbox("Choose an assistant", list(assistants.keys()), format_func=lambda x: assistants[x])
    st.sidebar.file_uploader(
        "Upload a file",
        type=["txt", "pdf", "png", "jpg", "jpeg", "csv", "json", "geojson", "xlsx", "xls"]
    )
    st.sidebar.button("Download Chat as CSV")

    user_msg = st.chat_input(
        "What is your query?", on_submit=disable_form, disabled=st.session_state.in_progress
    )

    if user_msg:
        st.session_state.user_msg = user_msg

    if "user_msg" in st.session_state:
        render_chat()
        with st.chat_message("user"):
            st.markdown(st.session_state.user_msg, True)
        st.session_state.chat_log.append({"name": "user", "msg": st.session_state.user_msg})

        run_stream(st.session_state.user_msg, assistant_id)
        st.session_state.in_progress = False
        st.session_state.user_msg = ""
        st.rerun()

    render_chat()

if __name__ == "__main__":
    main()
