import os
import openai
import streamlit as st
from openai import AssistantEventHandler
from typing_extensions import override
import pandas as pd

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
        # Clean the text to remove annotations and extract citations
        clean_text = text.value if hasattr(text, 'annotations') else text
        citations = [(ann.text, ann.file_citation.text) for ann in text.annotations] if hasattr(text, 'annotations') else []
        st.session_state.current_markdown.markdown(clean_text, True)
        st.session_state.chat_log.append({"name": "assistant", "msg": clean_text, "citations": citations})

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
    html_content = generate_html_with_tooltips(st.session_state.chat_log)
    add_tooltip_css()
    st.components.v1.html(html_content, height=600)

def download_chat_as_csv():
    df = pd.DataFrame(st.session_state.chat_log)
    csv = df.to_csv(index=False)
    st.download_button(label="Download Chat as CSV", data=csv, file_name='chat_log.csv', mime='text/csv')

def generate_html_with_tooltips(chat_log):
    html_content = ""
    for chat in chat_log:
        if chat["name"] == "assistant" and chat["citations"]:
            msg_with_tooltips = chat["msg"]
            for citation, source_text in chat["citations"]:
                msg_with_tooltips = msg_with_tooltips.replace(
                    citation,
                    f'<span class="tooltip">{citation}<span class="tooltiptext">{source_text}</span></span>'
                )
            html_content += f'<div class="chat-message assistant">{msg_with_tooltips}</div>'
        else:
            html_content += f'<div class="chat-message {chat["name"]}">{chat["msg"]}</div>'
    return html_content

def add_tooltip_css():
    tooltip_css = """
    <style>
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted black;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 120px;
        background-color: black;
        color: #fff;
        text-align: center;
        border-radius: 5px;
        padding: 5px 0;
        position: absolute;
        z-index: 1;
        bottom: 125%; /* Position the tooltip above the text */
        left: 50%;
        margin-left: -60px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    .chat-message {
        margin: 10px 0;
    }
    .chat-message.user {
        color: blue;
    }
    .chat-message.assistant {
        color: green;
    }
    </style>
    """
    st.markdown(tooltip_css, unsafe_allow_html=True)

if "tool_calls" not in st.session_state:
    st.session_state.tool_calls = []

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "in_progress" not in st.session_state:
    st.session_state.in_progress = False

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

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
        st.title("Assistant Selector")
        assistant_selection = st.selectbox(
            "Choose an assistant",
            list(assistants.keys()),
            format_func=lambda x: assistants[x]
        )
        assistant_id = assistant_ids[assistant_selection]

        user_msg = st.chat_input(
            "Message", on_submit=disable_form, disabled=st.session_state.in_progress
        )

        uploaded_file = st.sidebar.file_uploader(
            "Upload a file",
            type=[
                "txt", "pdf", "png", "jpg", "jpeg", "csv", "json", "geojson", "xlsx", "xls"
            ],
            disabled=st.session_state.in_progress,
        )

        if user_msg:
            render_chat()
            with st.chat_message("user"):
                st.markdown(user_msg, True)
            st.session_state.chat_log.append({"name": "user", "msg": user_msg, "citations": []})

            file = None
            if uploaded_file is not None:
                file = handle_uploaded_file(uploaded_file)
            run_stream(user_msg, file, assistant_id)
            st.session_state.in_progress = False
            st.rerun
                render_chat()
    download_chat_as_csv()
    if name == “main”:
main()
