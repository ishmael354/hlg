import streamlit as st
import openai
import pandas as pd
from datetime import datetime

# Title of the app
st.title("HLG_PT - Advanced Social Listening Tool")

# Function to authenticate user
def authenticate(username, password):
    if username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]:
        return True
    return False

# Function to create a thread
def create_thread(messages):
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    return response

# Function to create a run with instructions and tools
def create_run(thread_id, assistant_id, model="gpt-4", instructions=None, tools=None):
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    data = {
        "thread_id": thread_id,
        "assistant_id": assistant_id,
        "model": model,
    }
    if instructions:
        data["instructions"] = instructions
    if tools:
        data["tools"] = tools

    response = openai.Completion.create(**data)
    return response

# Function to list messages in a thread
def list_messages(thread_id):
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    response = openai.ChatCompletion.list(
        model="gpt-4",
        thread_id=thread_id
    )
    return response

# Function to get the assistant's response
def get_assistant_response(thread_id):
    messages = list_messages(thread_id)
    return messages['choices'][0]['message']['content']

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

        # Create thread and run
        messages = [{"role": "user", "content": prompt}]
        thread_response = create_thread(messages)
        thread_id = thread_response['id']

        run_response = create_run(thread_id, st.session_state["assistant_id"])
        response = get_assistant_response(thread_id)
        
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    # File upload
    uploaded_file = st.file_uploader("Upload a file")
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        st.session_state.messages.append({"role": "user", "content": content})
        with st.chat_message("user"):
            st.markdown(content)

        # Create thread with file attachment and run
        messages = [{
            "role": "user",
            "content": "Create 3 data visualizations based on the trends in this file.",
            "attachments": [
                {
                    "file_id": uploaded_file.id,
                    "tools": [{"type": "code_interpreter"}]
                }
            ]
        }]
        thread_response = create_thread(messages)
        thread_id = thread_response['id']

        run_response = create_run(thread_id, st.session_state["assistant_id"], tools=[{"type": "code_interpreter"}])
        response = get_assistant_response(thread_id)
        
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
