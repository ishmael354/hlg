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
        if snapshot.value:
            self.current_text = snapshot.value
            st.session_state.current_message = snapshot.value
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

def handle_tool_call(action):
    function_return = {}
    args = json.loads(action.function.arguments)
    match action.function.name:
        case 'run_command':
            function_return = {"tool_call_id": action.id, "output": run_command(args['hostname'], args['command'])}
        case 'print_working_dir_files':
            path = args.get('path', '')
            function_return = {"tool_call_id": action.id, "output": print_working_dir_files(path)}
        case 'read_file':
            function_return = {"tool_call_id": action.id, "output": read_file(args['path'])}
        case 'write_file':
            function_return = {"tool_call_id": action.id, "output": write_file(args['path'], args['contents'])}
        case _:
            function_return = {"tool_call_id": action.id, "output": 'Function does not exist'}
    return function_return
