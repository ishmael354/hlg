import os
import openai
import streamlit as st
from openai import AssistantEventHandler
from typing_extensions import override
import pandas as pd
import streamlit.components.v1 as components
from utils import generate_html_with_citations, add_tooltip_css

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Verify that all secrets are loaded
required_secrets = [
    "ASSISTANT1_ID", "ASSISTANT2_ID", "ASSISTANT3_ID", "ASSISTANT4_ID",
    "USERNAME", "PASSWORD"
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
        try:
            clean_text = text.value if hasattr(text, 'annotations') else text
            citations = [(ann.text, ann.file_citation.text) for ann in getattr(text, 'annotations', [])]
            citation_numbers = {ann.text: idx + 1 for idx, ann in enumerate(getattr(text, 'annotations', []))}
            formatted_text = clean_text
            for citation, number in citation_numbers.items():
                formatted_text = formatted_text.replace(citation, f"[{number}]")
            st.session_state.current_markdown.markdown(formatted_text, True)
            st.session_state.chat_log.append({"name": "assistant", "msg": formatted_text, "citations": citations})
        except AttributeError as e:
            st.error(f"Error processing text: {e}")

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

def create_thread():
    thread = openai.beta.threads.create()
    return thread

def create_message(thread, content, file):
    attachments = []
    if file is not None:
        attachments.append({"file_id": file.id, "tools": [{"type": "code_interpreter"}]})
    openai.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=content, attachments=attachments
    )

def run_stream(user_input, file, assistant_id):
    if "thread" not in st.session_state:
        st.session_state.thread = create_thread()
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
    try:
        html_content = generate_html_with_citations(st.session_state.chat_log)
        add_tooltip_css()
        components.html(html_content, height=600, scrolling=True)
    except Exception as e:
        st.error(f"Error rendering chat: {e}")

def download_chat_as_csv():
    df = pd.DataFrame(st.session_state.chat_log)
    csv = df.to_csv(index=False)
    return csv

if "tool_calls" not in st.session_state:
    st.session_state.tool_calls = []

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "in_progress" not in st.session_state:
    st.session_state.in_progress = False

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "citations" not in st.session_state:
    st.session_state.citations = []

def login(username, password):
    return username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]

def disable_form():
    st.session_state.in_progress = True

def main():
    if not st.session_state.logged_in:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
    else:
        st.sidebar.title("Assistant Selector")
        assistant_selection = st.sidebar.selectbox(
            "Choose an assistant",
            list(assistants.keys()),
            format_func=lambda x: assistants[x]
        )
        assistant_id = assistant_ids[assistant_selection]

        uploaded_file = st.sidebar.file_uploader(
            "Upload a file",
            type=[
                "txt", "pdf", "png", "jpg", "jpeg", "csv", "json", "geojson", "xlsx", "xls"
            ],
            disabled=st.session_state.in_progress,
        )

        csv_data = download_chat_as_csv()
        st.sidebar.download_button(label="Download Chat as CSV", data=csv_data, file_name='chat_log.csv', mime='text/csv')

        st.title("AI Assistant Chat")
        st.subheader("Ask questions about your dataset")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("What are some trends in this data set?"):
                st.session_state.user_msg = "What are some trends in this data set?"

        with col2:
            if st.button("Suggest some visualizations to make based on this data"):
                st.session_state.user_msg = "Suggest some visualizations to make based on this data"

        with col3:
            if st.button("Tell me some unexpected findings in the data set"):
                st.session_state.user_msg = "Tell me some unexpected findings in the data set"

        user_msg = st.chat_input(
            "What is your query?", on_submit=disable_form, disabled=st.session_state.in_progress
        )

        if user_msg:
            st.session_state.user_msg = user_msg

        if "user_msg" in st.session_state and st.session_state.user_msg:
            render_chat()
            with st.chat_message("user"):
                st.markdown(st.session_state.user_msg, True)
            st.session_state.chat_log.append({"name": "user", "msg": st.session_state.user_msg, "citations": []})

            file = None
            if uploaded_file is not None:
                file = handle_uploaded_file(uploaded_file)
            run_stream(st.session_state.user_msg, file, assistant_id)
            st.session_state.in_progress = False
            st.session_state.user_msg = ""
            st.rerun()

        render_chat()

        st.sidebar.title("Citations")
        if st.session_state.citations:
for idx, (citation_text, citation_source) in enumerate(st.session_state.citations, 1):
st.sidebar.write(f”{idx}. {citation_text}: {citation_source}”)

if name == “main”:
main()
