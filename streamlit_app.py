import os
import openai
import streamlit as st
from openai import AssistantEventHandler
from typing_extensions import override

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Verify that all required secrets are loaded
required_secrets = [
    "ASSISTANT_1_ID", "ASSISTANT_2_ID", "ASSISTANT_3_ID", "ASSISTANT_4_ID",
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
    "assistant_1": st.secrets["ASSISTANT_1_ID"],
    "assistant_2": st.secrets["ASSISTANT_2_ID"],
    "assistant_3": st.secrets["ASSISTANT_3_ID"],
    "assistant_4": st.secrets["ASSISTANT_4_ID"]
}

def create_thread(content):
    messages = [
        {
            "role": "user",
            "content": content,
        }
    ]
    thread = openai.beta.threads.create()
    return thread

def create_message(thread, content):
    openai.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=content
    )

def run_stream(user_input, assistant_id):
    if "thread" not in st.session_state:
        st.session_state.thread = create_thread(user_input)
    create_message(st.session_state.thread, user_input)
    with openai.beta.threads.runs.stream(
        thread_id=st.session_state.thread.id,
        assistant_id=assistant_id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

def main():
    st.title("AI Assistant Chat")
    st.markdown("### Ask questions about your dataset")

    sample_queries = ["What are some trends in this data set?", "Suggest some visualizations to make based on this data", "Tell me some unexpected findings in the data set"]
    cols = st.columns(len(sample_queries))

    for i, query in enumerate(sample_queries):
        with cols[i]:
            if st.button(query):
                st.session_state.user_msg = query

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
        ]
    )

    if "user_msg" in st.session_state:
        render_chat()
        with st.chat_message("user"):
            st.markdown(st.session_state.user_msg, True)
        st.session_state.chat_log.append({"name": "user", "msg": st.session_state.user_msg})

        run_stream(st.session_state.user_msg, st.session_state.assistant_id)
        st.session_state.in_progress = False
        st.session_state.user_msg = ""
        st.rerun()

    render_chat()

    if st.button("Download Chat as CSV"):
        download_chat_as_csv()

if __name__ == "__main__":
    main()
