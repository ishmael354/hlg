import openai
import re
from openai import AssistantEventHandler
from typing_extensions import override
import streamlit as st

class EventHandler(AssistantEventHandler):
    def __init__(self):
        self.current_text = ""

    @override
    def on_event(self, event):
        pass

    @override
    def on_text_created(self, text):
        self.current_text = ""
        st.session_state.current_message = ""
        with st.chat_message("Assistant"):
            st.session_state.current_markdown = st.empty()

    @override
    def on_text_delta(self, delta, snapshot):
        if snapshot['value']:
            self.current_text = snapshot['value']
            st.session_state.current_message = snapshot['value']
            st.session_state.current_markdown.markdown(st.session_state.current_message, True)

    @override
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
