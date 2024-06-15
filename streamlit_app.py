import os
import openai
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from utils import generate_html_with_citations, add_tooltip_css
from event_handler import EventHandler
import re

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

def create_thread():
    return openai.beta.threads.create()

def create_message(thread, content, file):
    attachments = []
    if file is not None:
        attachments.append({"file_id": file.id, "tools": [{"type": "code_interpreter"}]})
    openai.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=content, attachments=attachments
    )

def handle_uploaded_file(uploaded_file):
    return openai.files.create(file=uploaded_file, purpose="assistants")

def clean_message_content(message):
    for part in message['content']:
        if 'text' in part:
            part['text'] = re.sub(r'【[^】]+】', '', part['text'])
            part['text'] = re.sub(r'sandbox:[^\s]+', '', part['text'])

def render_chat():
    try:
        html_content = generate_html_with_citations(st.session_state.chat_log)
        add_tooltip_css()
        components.html(html_content, height=600, scrolling=True)
    except Exception as e:
        st.error(f"Error rendering chat: {e}")

def download_chat_as_csv():
    df = pd.DataFrame(st.session_state.chat_log)
    return df.to_csv(index=False)

if "tool_calls" not in st.session_state:
    st.session_state.tool_calls = []

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "in_progress" not in st.session_state:
    st.session_state.in_progress = False

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "thinking" not in st.session_state:
    st.session_state.thinking = False

def login(username, password):
    return username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]

def disable_form():
    st.session_state.in_progress = True
    st.session_state.thinking = True

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
        st.session_state.assistant_id = assistant_ids[assistant_selection]

        uploaded_file = st.sidebar.file_uploader(
            "Upload a file",
            type=[
                "txt", "pdf", "png", "jpg", "jpeg", "csv", "json", "geojson", "xlsx", "xls"
            ],
            disabled=st.session_state.in_progress,
        )

        csv_data = download_chat_as_csv()
        st.sidebar.download_button(label="Download Chat as CSV", data=csv_data, file_name='chat_log.csv', mime='text/csv')

        # Create a fixed top bar
        st.markdown(
            """
            <style>
            .fixed-header {
                position: -webkit-sticky;
                position: sticky;
                top: 0;
                width: 100%;
                background-color: #fff;
                z-index: 9999;
                padding-top: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #ccc;
            }
            .fixed-header .stButton { 
                display: inline-block; 
                margin-right: 10px; 
            }
            </style>
            """, unsafe_allow_html=True)

        st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
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

        st.markdown('</div>', unsafe_allow_html=True)

        user_msg = st.chat_input(
            "What is your query?", on_submit=disable_form, disabled=st.session_state.in_progress
        )

        if user_msg:
            st.session_state.user_msg = user_msg

        if "user_msg" in st.session_state and st.session_state.user_msg:
            render_chat()
            with st.chat_message("user"):
                st.markdown(st.session_state.user_msg, True)
            st.session_state.chat_log.append({"name": "user", "msg": st.session_state.user_msg})

            file = None
            if uploaded_file is not None:
                file = handle_uploaded_file(uploaded_file)

            with st.spinner("Thinking..."):
                try:
                    thread = create_thread()
                    create_message(thread, st.session_state.user_msg, file)
                    response = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=st.session_state.assistant_id)
                    
                    if 'messages' in response:
                        for message in response['messages']:
                            clean_message_content(message)
                            st.session_state.chat_log.append({"name": "assistant", "msg": message['content'][0]['text']})
                    else:
                        st.error("No messages found in the response.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

            st.session_state.in_progress = False
            st.session_state.thinking = False
            st.session_state.user_msg = ""
            st.experimental_rerun()

        render_chat()

if __name__ == "__main__":
    main()
