import streamlit as st
import openai
from typing_extensions import override
from openai import AssistantEventHandler
import os

# Load secrets from Streamlit
openai_api_key = st.secrets["OPENAI_API_KEY"]

# Configure OpenAI client
openai.api_key = openai_api_key

# Configuration for assistants
assistant_titles = {
    "assistant_1": st.secrets["ASSISTANT_1_TITLE"],
    "assistant_2": st.secrets["ASSISTANT_2_TITLE"],
    "assistant_3": st.secrets["ASSISTANT_3_TITLE"],
    "assistant_4": st.secrets["ASSISTANT_4_TITLE"],
}
assistants = {
    "assistant_1": st.secrets["ASSISTANT_1_ID"],
    "assistant_2": st.secrets["ASSISTANT_2_ID"],
    "assistant_3": st.secrets["ASSISTANT_3_ID"],
    "assistant_4": st.secrets["ASSISTANT_4_ID"],
}

# Event handler class
class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
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
        st.session_state.current_markdown.markdown(text, True)
        st.session_state.chat_log.append({"role": "assistant", "content": text})

    @override
    def on_tool_call_created(self, tool_call):
        st.session_state.current_tool_input = ""
        with st.chat_message("Assistant"):
            st.session_state.current_tool_input_markdown = st.empty()

    @override
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                st.session_state.current_tool_input += delta.code_interpreter.input
                input_code = f"### code interpreter\ninput:\n```python\n{st.session_state.current_tool_input}\n```"
                st.session_state.current_tool_input_markdown.markdown(input_code, True)

    @override
    def on_tool_call_done(self, tool_call):
        st.session_state.tool_calls.append(tool_call)
        if tool_call.type == "code_interpreter":
            input_code = f"### code interpreter\ninput:\n```python\n{tool_call.code_interpreter.input}\n```"
            st.session_state.current_tool_input_markdown.markdown(input_code, True)
            st.session_state.chat_log.append({"role": "assistant", "content": input_code})
            st.session_state.current_tool_input_markdown = None

# Function to create a thread
def create_thread():
    return openai.beta.threads.create()

# Function to create a message
def create_message(thread_id, content):
    return openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    )

# Function to handle file uploads
def handle_uploaded_file(uploaded_file):
    return openai.files.create(file=uploaded_file, purpose="assistants")

# Function to run the assistant stream
def run_stream(user_input, file, assistant_id):
    if "thread" not in st.session_state:
        st.session_state.thread = create_thread()
    create_message(st.session_state.thread.id, user_input)
    with openai.beta.threads.runs.stream(
        thread_id=st.session_state.thread.id,
        assistant_id=assistant_id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

# Function to render chat
def render_chat():
    for chat in st.session_state.chat_log:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"], True)

# App initialization
if "tool_calls" not in st.session_state:
    st.session_state.tool_calls = []

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "in_progress" not in st.session_state:
    st.session_state.in_progress = False

def disable_form():
    st.session_state.in_progress = True

# Main function
def main():
    selected_assistant = st.sidebar.selectbox(
        "Choose an Assistant",
        options=list(assistants.keys()),
        format_func=lambda x: assistant_titles[x]
    )

    st.title(assistant_titles[selected_assistant])
    user_msg = st.chat_input("Message", on_submit=disable_form, disabled=st.session_state.in_progress)

    uploaded_file = st.sidebar.file_uploader("Upload a file", type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'csv', 'json', 'geojson', 'xlsx', 'xls'], disabled=st.session_state.in_progress)

    if user_msg:
        render_chat()
        with st.chat_message("user"):
            st.markdown(user_msg, True)
        st.session_state.chat_log.append({"role": "user", "content": user_msg})

        file = handle_uploaded_file(uploaded_file) if uploaded_file else None
        run_stream(user_msg, file, assistants[selected_assistant])
        st.session_state.in_progress = False
        st.session_state.tool_call = None
        st.experimental_rerun()

    render_chat()

if __name__ == "__main__":
    main()
