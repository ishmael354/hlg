import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import openai
from openai import AssistantEventHandler
from typing_extensions import override

# Title of the app
st.title("HLG_PT - Advanced Social Listening Tool")

# Function to authenticate user
def authenticate(username, password):
    if username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]:
        return True
    return False

# Custom event handler for streaming responses
class StreamlitEventHandler(AssistantEventHandler):
    def __init__(self, container):
        self.container = container
        self.text = ""

    @override
    def on_text_created(self, text) -> None:
        self.text = text
        self.update_container()

    @override
    def on_text_delta(self, delta, snapshot):
        self.text += delta.value
        self.update_container()

    def on_tool_call_created(self, tool_call):
        self.text += f"\n{tool_call.type}\n"
        self.update_container()

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                self.text += delta.code_interpreter.input
                self.update_container()
            if delta.code_interpreter.outputs:
                self.text += "\n\noutput >"
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        self.text += f"\n{output.logs}"
                        self.update_container()

    def update_container(self):
        self.container.markdown(self.text)

# Function to get the assistant's response
def get_assistant_response(openai, thread_id, run_id, container):
    event_handler = StreamlitEventHandler(container)
    with openai.Threads.runs.stream(
        thread_id=thread_id,
        assistant_id=st.session_state["assistant_id"],
        event_handler=event_handler,
    ) as stream:
        stream.until_done()

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

        with st.chat_message("assistant") as container:
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            if not st.session_state.get("thread"):
                thread = openai.Threads.create()
                st.session_state["thread"] = thread
            else:
                thread = st.session_state["thread"]

            openai.Threads.create_message(thread['id'], {"role": "user", "content": prompt})
            run = openai.Threads.create_run(thread['id'], {"assistant_id": st.session_state["assistant_id"]})
            get_assistant_response(openai, thread['id'], run['id'], container)

    # File upload
    uploaded_file = st.file_uploader("Upload a file")
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        st.session_state.messages.append({"role": "user", "content": content})
        with st.chat_message("user"):
            st.markdown(content)

        with st.chat_message("assistant") as container:
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            if not st.session_state.get("thread"):
                thread = openai.Threads.create()
                st.session_state["thread"] = thread
            else:
                thread = st.session_state["thread"]

            openai.Threads.create_message(thread['id'], {"role": "user", "content": content})
            run = openai.Threads.create_run(thread['id'], {"assistant_id": st.session_state["assistant_id"]})
            get_assistant_response(openai, thread['id'], run['id'], container)

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
