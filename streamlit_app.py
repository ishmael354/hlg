import openai
import streamlit as st
import re
import time
from event_handler import EventHandler, handle_tool_call

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

def create_message(thread, user_input, file=None):
    if file:
        return openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input,
            file_ids=[file.id]
        )
    else:
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
            if event['status'] == 'requires_action':
                action_outputs = []
                for action in event['required_action']['submit_tool_outputs']['tool_calls']:
                    function_return = handle_tool_call(action)
                    action_outputs.append(function_return)
                run = openai.beta.threads.runs.submit_tool_outputs(
                    thread_id=st.session_state.thread.id,
                    run_id=run.id,
                    tool_outputs=action_outputs
                )
            time.sleep(0.2)
    except Exception as e:
        st.error(f"Error running stream: {str(e)}")

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
