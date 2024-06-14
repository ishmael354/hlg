import streamlit as st
import openai
import time
import pandas as pd
from datetime import datetime

# Initialize OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Title of the app
st.title("HLG_PT - Advanced Social Listening Tool")

# Function to authenticate user
def authenticate(username, password):
    if username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]:
        return True
    return False

# Function to handle API errors
def handle_api_error(e):
    st.error(f"API error: {str(e)}")
    st.stop()

# Function to create a thread
def create_thread():
    try:
        return openai.Thread.create()
    except openai.error.OpenAIError as e:
        handle_api_error(e)

# Function to create a message
def create_message(thread_id, content, file_ids=None):
    try:
        return openai.Thread.create_message(thread_id, {"role": "user", "content": content, "file_ids": file_ids})
    except openai.error.OpenAIError as e:
        handle_api_error(e)

# Function to create a run
def create_run(thread_id, assistant_id):
    try:
        return openai.Thread.create_run(thread_id, {"assistant_id": assistant_id})
    except openai.error.OpenAIError as e:
        handle_api_error(e)

# Function to get the assistant's response
def get_assistant_response(thread_id, run_id):
    try:
        while True:
            steps = openai.Thread.list_run_steps(thread_id, run_id)
            if steps['data']:
                for step in steps['data']:
                    if step['status'] == "completed":
                        message_id = step['step_details']['message_creation']['message_id']
                        message = openai.Thread.retrieve_message(message_id, thread_id)
                        return message['content'][0]['text']['value']
                    elif step['status'] == "failed":
                        handle_api_error(f"Step failed: {step['last_error']}")
            time.sleep(0.2)
    except openai.error.OpenAIError as e:
        handle_api_error(e)

# Login form
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    with st.form("login"):
        st.write("Log In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state["authenticated"] = authenticate(username, password)
            if not st.session_state["authenticated"]:
                st.error("Invalid username or password")
else:
    # Model selection
    models = {
        "Assistant 1": st.secrets["ASSISTANT1_ID"],
        "Assistant 2": st.secrets["ASSISTANT2_ID"],
        "Assistant 3": st.secrets["ASSISTANT3_ID"],
        "Assistant 4": st.secrets["ASSISTANT4_ID"]
    }
    selected_model = st.selectbox("Choose an Assistant", list(models.keys()))
    st.session_state["assistant_id"] = models[selected_model]

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What is your query?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if not st.session_state.get("thread"):
                thread = create_thread()
                st.session_state["thread"] = thread
            else:
                thread = st.session_state["thread"]

            create_message(thread['id'], prompt)
            run = create_run(thread['id'], st.session_state["assistant_id"])
            response = get_assistant_response(thread['id'], run['id'])
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    # File upload
    uploaded_file = st.file_uploader("Upload a file")
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        st.session_state.messages.append({"role": "user", "content": content})
        with st.chat_message("user"):
            st.markdown(content)

        with st.chat_message("assistant"):
            if not st.session_state.get("thread"):
                thread = create_thread()
                st.session_state["thread"] = thread
            else:
                thread = st.session_state["thread"]

            create_message(thread['id'], content)
            run = create_run(thread['id'], st.session_state["assistant_id"])
            response = get_assistant_response(thread['id'], run['id'])
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    # Save chat history
    if st.button("Save Chat History"):
        chat_df = pd.DataFrame(st.session_state.messages)
        chat_df.to_csv(f"chat_history_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        st.success("Chat history saved!")

    # Log out
    if st.button("Log Out"):
        st.session_state["authenticated"] = False
        st.session_state.messages = []
