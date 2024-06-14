import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Title of the app
st.title("HLG_PT - Advanced Social Listening Tool")

# Function to authenticate user
def authenticate(username, password):
    if username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]:
        return True
    return False

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
    # Flowise chat flow selection
    flowise_flows = {
        "Flow 1": st.secrets["FLOW1_ENDPOINT"],
        "Flow 2": st.secrets["FLOW2_ENDPOINT"],
        "Flow 3": st.secrets["FLOW3_ENDPOINT"],
        "Flow 4": st.secrets["FLOW4_ENDPOINT"]
    }
    selected_flow = st.selectbox("Choose a Data Set", list(flowise_flows.keys()))
    st.session_state["flow_endpoint"] = flowise_flows[selected_flow]

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
            payload = {
                "question": prompt,
                "overrideConfig": {
                    "selectedAssistant": "Social_Listening_Expert",  # Replace with the correct assistant name
                    "disableFileDownload": True
                }
            }
            try:
                response = requests.post(st.session_state["flow_endpoint"], json=payload)
                st.write("Response from Flowise:", response.text)  # Debugging: Print the response to check its structure
                response_json = response.json()

                # Check if the response contains the expected content
                if "content" in response_json:
                    st.markdown(response_json["content"])
                    st.session_state.messages.append({"role": "assistant", "content": response_json["content"]})
                else:
                    st.error("Unexpected response format from Flowise")
            except Exception as e:
                st.error(f"Error while fetching response: {e}")

    # File upload
    uploaded_file = st.file_uploader("Upload a file")
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        st.session_state.messages.append({"role": "user", "content": content})
        with st.chat_message("user"):
            st.markdown(content)

        with st.chat_message("assistant"):
            payload = {
                "question": content,
                "overrideConfig": {
                    "selectedAssistant": "Social_Listening_Expert",  # Replace with the correct assistant name
                    "disableFileDownload": True
                }
            }
            try:
                response = requests.post(st.session_state["flow_endpoint"], json=payload)
                st.write("Response from Flowise:", response.text)  # Debugging: Print the response to check its structure
                response_json = response.json()

                # Check if the response contains the expected content
                if "content" in response_json:
                    st.markdown(response_json["content"])
                    st.session_state.messages.append({"role": "assistant", "content": response_json["content"]})
                else:
                    st.error("Unexpected response format from Flowise")
            except Exception as e:
                st.error(f"Error while fetching response: {e}")

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
