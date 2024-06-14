import streamlit as st
import openai
import pandas as pd
from datetime import datetime
import time

# Title of the app
st.title("HLG_PT - Advanced Social Listening Tool")

# Function to authenticate user
def authenticate(username, password):
    if username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]:
        return True
    return False

# Function to create a thread
def create_thread(client):
    thread = client.beta.threads.create()
    return thread

# Function to add a message to the thread
def add_message_to_thread(client, thread_id, role, content):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=content
    )
    return message

# Function to create a run
def create_run(client, thread_id, assistant_id):
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    return run

# Function to get run steps
def get_run_steps(client, thread_id, run_id):
    steps = client.beta.threads.runs.steps.list(
        thread_id=thread_id,
        run_id=run_id
    )
    return steps

# Function to retrieve message
def retrieve_message(client, message_id, thread_id):
    message = client.beta.threads.messages.retrieve(
        message_id=message_id,
        thread_id=thread_id
    )
    return message

# Initialize OpenAI client
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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

    # Create a thread if not exists
    if "thread_id" not in st.session_state:
        thread = create_thread(client)
        st.session_state["thread_id"] = thread.id

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What is your query?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Add message to thread
        add_message_to_thread(client, st.session_state["thread_id"], "user", prompt)

        # Create a run
        run = create_run(client, st.session_state["thread_id"], st.session_state["assistant_id"])

        # Display a loading spinner
        with st.spinner("Thinking..."):
            while True:
                steps = get_run_steps(client, st.session_state["thread_id"], run.id)
                st.write(steps)  # Log the steps to Streamlit interface for debugging
                if 'data' in steps and steps['data']:
                    status = steps['data'][0]['status']
                    st.write(f"Run status: {status}")  # Log the status
                    if status == "completed":
                        break
                else:
                    st.write("No data in steps")
                time.sleep(1)  # Wait for 1 second before checking again

            # Retrieve message
            if 'data' in steps and steps['data']:
                for step in steps['data']:
                    if step['status'] == "completed" and step['type'] == "message_creation":
                        message_id = step['step_details']['message_creation']['message_id']
                        message = retrieve_message(client, message_id, st.session_state["thread_id"])
                        response = message['content'][0]['text']['value']
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        break
            else:
                st.error("Failed to retrieve steps data")

    # File upload
    uploaded_file = st.file_uploader("Upload a file")
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        st.session_state.messages.append({"role": "user", "content": content})
        with st.chat_message("user"):
            st.markdown(content)

        # Add message to thread with file attachment
        add_message_to_thread(client, st.session_state["thread_id"], "user", content)

        # Create a run
        run = create_run(client, st.session_state["thread_id"], st.session_state["assistant_id"])

        # Display a loading spinner
        with st.spinner("Thinking..."):
            while True:
                steps = get_run_steps(client, st.session_state["thread_id"], run.id)
                st.write(steps)  # Log the steps to Streamlit interface for debugging
                if 'data' in steps and steps['data']:
                    status = steps['data'][0]['status']
                    st.write(f"Run status: {status}")  # Log the status
                    if status == "completed":
                        break
                else:
                    st.write("No data in steps")
                time.sleep(1)  # Wait for 1 second before checking again

            # Retrieve message
            if 'data' in steps and steps['data']:
                for step in steps['data']:
                    if step['status'] == "completed" and step['type'] == "message_creation":
                        message_id = step['step_details']['message_creation']['message_id']
                        message = retrieve_message(client, message_id, st.session_state["thread_id"])
                        response = message['content'][0]['text']['value']
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        break
            else:
                st.error("Failed to retrieve steps data")

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
