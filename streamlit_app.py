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
            clean_message = re.sub(r'【[^】]+】', '', snapshot.value)
            st.session_state.current_message = clean_message
            st.session_state.current_markdown.markdown(st.session_state.current_message, True)

    @override
    def on_text_done(self, text):
        clean_text = re.sub(r'【[^】]+】', '', text)
        st.session_state.current_markdown.markdown(clean_text, True)
        st.session_state.chat_log.append({"name": "assistant", "msg": clean_text})

def run_stream(user_input, assistant_id):
    thread = openai.beta.threads.create()
    message = openai.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_input
    )
    with openai.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant_id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

def render_chat():
    for chat in st.session_state.chat_log:
        with st.chat_message(chat["name"]):
            st.markdown(chat["msg"], True)

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "in_progress" not in st.session_state:
    st.session_state.in_progress = False

def main():
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

    st.sidebar.button("Download Chat as CSV")

    st.title("AI Assistant Chat")
    st.header("Ask questions about your dataset")

    sample_queries = [
        "What are some trends in this data set?",
        "Suggest some visualizations to make based on this data",
        "Tell me some unexpected findings in the data set"
    ]

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(sample_queries[0]):
            st.session_state.user_msg = sample_queries[0]
            st.session_state.in_progress = True

    with col2:
        if st.button(sample_queries[1]):
            st.session_state.user_msg = sample_queries[1]
            st.session_state.in_progress = True

    with col3:
        if st.button(sample_queries[2]):
            st.session_state.user_msg = sample_queries[2]
            st.session_state.in_progress = True

    user_msg = st.chat_input("What is your query?", disabled=st.session_state.in_progress)

    if user_msg:
        st.session_state.user_msg = user_msg
        st.session_state.in_progress = True

    if "user_msg" in st.session_state:
        render_chat()
        with st.chat_message("user"):
            st.markdown(st.session_state.user_msg, True)
        st.session_state.chat_log.append({"name": "user", "msg": st.session_state.user_msg, "citations": []})

        file = None
        if uploaded_file is not None:
            file = openai.File.create(file=uploaded_file, purpose="assistants")

        run_stream(st.session_state.user_msg, assistant_id)
        st.session_state.in_progress = False
        st.session_state.user_msg = ""
        st.rerun()

    render_chat()

if __name__ == "__main__":
    main()
