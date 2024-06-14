import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import openai  # Import the OpenAI package

# Title of the app
st.title("HLG_PT - Advanced Social Listening Tool")

# Function to authenticate user
def authenticate(username, password):
    if username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]:
        return True
    return False

# Function to initiate interaction
def initiate_interaction(user_message, uploaded_file):
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    thread = openai.Threads.create()
    openai.Threads.create_message(thread['id'], {"role": "user", "content": user_message})
    if uploaded_file:
        file_content = uploaded_file.read().decode("utf-8")
        openai.Threads.create_message(thread['id'], {"role": "user", "content": file_content})
    return thread

# Function to trigger assistant
def trigger_assistant(thread_id, assistant_id):
    run = openai.Threads.create_run(thread_id, {"assistant_id": assistant_id})
    return run

# Function to get assistant response
def get_assistant_response(openai, thread_id):
    messages = openai.Threads.list_messages(thread_id)
    return messages['data'][0]['content'][0]['text']['value']

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

        my_thread = initiate_interaction(prompt, None)
        run = trigger_assistant(my_thread['id'], st.session_state["assistant_id"])
        response = get_assistant_response(openai, my_thread['id'])
        
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    # File upload
    uploaded_file = st.file_uploader("Upload a file")
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        st.session_state.messages.append({"role": "user", "content": content})
        with st.chat_message("user"):
            st.markdown(content)

        my_thread = initiate_interaction(content, uploaded_file)
        run = trigger_assistant(my_thread['id'], st.session_state["assistant_id"])
        response = get_assistant_response(openai, my_thread['id'])
        
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

# Run the Streamlit app
if __name__ == "__main__":
    import os
    os.system("streamlit run main.py")
