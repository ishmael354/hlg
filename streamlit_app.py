import streamlit as st
import openai
import os
import pandas as pd
from datetime import datetime
from typing_extensions import override
from openai import AssistantEventHandler

# Initialize OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Title of the app
st.title("HLG_PT - Advanced Social Listening Tool")

# Function to authenticate user
def authenticate(username, password):
    return username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]

# Event handler class
class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)

# Function to create a thread
def create_thread():
    return openai.beta.threads.create()

# Function to create a message
def create_message(thread_id, content):
    return openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    )

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

            message = create_message(thread.id, prompt)

            try:
                with openai.beta.threads.runs.stream(
                    thread_id=thread.id,
                    assistant_id=st.session_state["assistant_id"],
                    instructions="Please address the user as Jane Doe. The user has a premium account.",
                    event_handler=EventHandler(),
                ) as stream:
                    stream.until_done()
            except BrokenPipeError:
                st.error("The connection was closed prematurely. Please try again.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

            response_content = message['content']
            st.session_state.messages.append({"role": "assistant", "content": response_content})
            st.markdown(response_content)

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

            message = create_message(thread.id, content)

            try:
                with openai.beta.threads.runs.stream(
                    thread_id=thread.id,
                    assistant_id=st.session_state["assistant_id"],
                    instructions="Please address the user as Jane Doe. The user has a premium account.",
                    event_handler=EventHandler(),
                ) as stream:
                    stream.until_done()
            except BrokenPipeError:
                st.error("The connection was closed prematurely. Please try again.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

            response_content = message['content']
            st.session_state.messages.append({"role": "assistant", "content": response_content})
            st.markdown(response_content)

    # Save chat history
    if st.button("Save Chat History"):
        chat_df = pd.DataFrame(st.session_state.messages)
        chat_df.to_csv(f"chat_history_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        st.success("Chat history saved!")

    # Log out
    if st.button("Log Out"):
        st.session_state["authenticated"] = False
        st.session_state.messages = []
