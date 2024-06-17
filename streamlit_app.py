import openai
import streamlit as st
import re
import time
from openai import AssistantEventHandler

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

def create_message(thread, user_input):
    return openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

def run_stream(user_input, assistant_id):
    if "thread" not in st.session_state:
        st.session_state.thread = openai.beta.threads.create()
    try:
        create_message(st.session_state.thread, user_input)
        handler = EventHandler()
        run = openai.beta.threads.runs.create(thread_id=st.session_state.thread.id, assistant_id=assistant_id)
        for event in run:
            handler.handle_event(event)
            time.sleep(0.2) # Sleep and check run status again
    except Exception as e:
        st.error(f"Error running stream: {str(e)}")

class EventHandler(AssistantEventHandler):
    def __init__(self):
        self.current_text = ""

    def on_event(self, event):
        st.write(f"Event received: {event}")

    def on_text_created(self, text):
        self.current_text = ""
        st.session_state.current_message = ""
        with st.chat_message("Assistant"):
            st.session_state.current_markdown = st.empty()

    def on_text_delta(self, delta, snapshot):
        if snapshot['value']:
            self.current_text = snapshot['value']
            st.session_state.current_message = snapshot['value']
            st.session_state.current_markdown.markdown(st.session_state.current_message, True)

    def on_text_done(self, text):
        clean_text = re.sub(r'【[^】]+】', '', self.current_text)
        st.session_state.current_markdown.markdown(clean_text, True)
        st.session_state.chat_log.append({"name": "assistant", "msg": clean_text})

    def handle_event(self, event):
        if event['type'] == 'text_created':
            self.on_text_created(event['data'])
        elif event['type'] == 'text_delta':
            self.on_text_delta(event['data'], event['snapshot'])
        elif event['type'] == 'text_done':
            self.on_text_done(event['data'])

def main():
    st.sidebar.title("AI Assistant Chat")
    assistant_id = assistant_ids[st.sidebar.selectbox("Choose an assistant", list(assistants.keys()))]
    uploaded_file = st.sidebar.file_uploader("Upload a file")

    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []

    st.sidebar.button("Download Chat as CSV", on_click=download_chat_log)

    for entry in st.session_state.chat_log:
        st.chat_message(entry["name"]).markdown(entry["msg"])

    user_msg = st.text_input("What is your query?")
    if user_msg:
        st.session_state.user_msg = user_msg
        run_stream(user_msg, assistant_id)

def download_chat_log():
    chat_log = st.session_state.chat_log
    # Your implementation for downloading the chat log

if __name__ == "__main__":
    main()
