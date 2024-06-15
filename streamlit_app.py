import os
import openai
import streamlit as st
from openai import AssistantEventHandler
from typing_extensions import override
import re

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Ensure required secrets are present
required_secrets = [
    "ASSISTANT_1_ID", "ASSISTANT_2_ID", "ASSISTANT_3_ID", "ASSISTANT_4_ID",
    "ASSISTANT_1_TITLE", "ASSISTANT_2_TITLE", "ASSISTANT_3_TITLE", "ASSISTANT_4_TITLE"
]

missing_secrets = [secret for secret in required_secrets if secret not in st.secrets]

if missing_secrets:
    st.error(f"Missing required secrets: {', '.join(missing_secrets)}")
    st.stop()

assistants = {
    "assistant_1": st.secrets["ASSISTANT_1_TITLE"],
    "assistant_2": st.secrets["ASSISTANT_2_TITLE"],
    "assistant_3": st.secrets["ASSISTANT_3_TITLE"],
    "assistant_4": st.secrets["ASSISTANT_4_TITLE"]
}

assistant_ids = {
    "assistant_1": st.secrets["ASSISTANT_1_ID"],
    "assistant_2": st.secrets["ASSISTANT_2_ID"],
    "assistant_3": st.secrets["ASSISTANT_3_ID"],
    "assistant_4": st.secrets["ASSISTANT_4_ID"]
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
            clean_message = re.sub(r'【[^】]+】', '', snapshot.value)
            st.session_state.current_message = clean_message
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

def create_thread(content, file):
    messages = [
        {
            "role": "user",
            "content": content,
        }
    ]
    if file is not None:
        messages[0].update({"file_ids": [file.id]})
    thread = openai.beta.threads.create()
    return thread

def create_message(thread, content, file):
    attachments = []
    if file is not None:
        attachments.append(
            {"file_id": file.id, "tools": [{"type": "code_interpreter"}]}
        )
    openai.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=content, attachments=attachments
    )

def run_stream(user_input, file, assistant_id):
    if "thread" not in st.session_state:
        st.session_state.thread = create_thread(user_input, file)
    create_message(st.session_state.thread, user_input, file)
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

if "tool_call" not in st.session_state:
    st.session_state.tool_calls = []

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "in_progress" not in st.session_state:
    st.session_state.in_progress = False

def disable_form():
    st.session_state.in_progress = True

def main():
    st.title("AI Assistant Chat")
    st.header("Ask questions about your dataset")

    sample_queries = [
        "What are some trends in this data set?",
        "Suggest some visualizations to make based on this data",
        "Tell me some unexpected findings in the data set"
    ]

    for query in sample_queries:
        if st.button(query):
            st.session_state.user_msg = query
            st.session_state.in_progress = True

    assistant_selection = st.sidebar.selectbox(
        "Choose an assistant",
        list(assistants.keys()),
        format_func=lambda x: assistants[x]
    )
    st.session_state.assistant_id = assistant_ids[assistant_selection]

    uploaded_file = st.sidebar.file_uploader(
        "Upload a file",
        type=[
            "txt", "pdf", "png", "jpg", "jpeg", "csv", "json", "geojson", "xlsx", "xls"
        ],
        disabled=st.session_state.in_progress,
    )

    if st.sidebar.button("Download Chat as CSV"):
        import pandas as pd
        df = pd.DataFrame(st.session_state.chat_log)
        df.to_csv("chat_history.csv", index=False)
        st.sidebar.download_button(
            label="Download CSV",
            data=df.to_csv().encode('utf-8'),
            file_name='chat_history.csv',
            mime='text/csv',
        )

    if "user_msg" in st.session_state:
        render_chat()
        with st.chat_message("user"):
            st.markdown(st.session_state.user_msg, True)
        st.session_state.chat_log.append({"name": "user", "msg": st.session_state.user_msg})

        file = None
        if uploaded_file is not None:
            file = handle_uploaded_file(uploaded_file)
        run_stream(st.session_state.user_msg, file, st.session_state.assistant_id)
        st.session_state.in_progress = False
        st.session_state.user_msg = ""
        st.rerun()

    render_chat()

if __name__ == "__main__":
    main()
