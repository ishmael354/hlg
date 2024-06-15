import re
from openai import AssistantEventHandler
from typing_extensions import override
import streamlit as st

class EventHandler(AssistantEventHandler):
    @override
    def on_event(self, event):
        pass

    @override
    def on_text_created(self, text):
        st.session_state.current_message = ""
        with st.chat_message("Assistant"):
            st.session_state.current_markdown = st.empty()

    @override
    def on_text_delta(self, delta, snapshot):
        if snapshot.value:
            try:
                clean_message = re.sub(r'【[^】]+】', '', str(snapshot.value))
                st.session_state.current_message = clean_message
                st.session_state.current_markdown.markdown(st.session_state.current_message, True)
            except Exception as e:
                st.error(f"Error processing text delta: {e}")

    @override
    def on_text_done(self, text):
        try:
            clean_text = re.sub(r'【[^】]+】', '', str(text))
            st.session_state.current_markdown.markdown(clean_text, True)
            st.session_state.chat_log.append({"name": "assistant", "msg": clean_text})
        except Exception as e:
            st.error(f"Error processing text done: {e}")
