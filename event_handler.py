import streamlit as st
from openai import AssistantEventHandler
from typing_extensions import override

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
            st.session_state.current_message = snapshot.value
            st.session_state.current_markdown.markdown(st.session_state.current_message, True)

    @override
    def on_text_done(self, text):
        try:
            clean_text = text.value
            citations = []
            if hasattr(text, 'annotations'):
                annotations = text.annotations
                citation_numbers = {ann.text: idx + 1 for idx, ann in enumerate(annotations)}
                for index, annotation in enumerate(annotations):
                    clean_text = clean_text.replace(annotation.text, f'[{index + 1}]')
                    if hasattr(annotation, 'file_citation'):
                        citations.append((f'[{index + 1}]', f'{annotation.file_citation.quote} from {annotation.file_citation.file_id}'))
                    elif hasattr(annotation, 'file_path'):
                        citations.append((f'[{index + 1}]', f'Click <here> to download {annotation.file_path.file_id}'))
            st.session_state.current_markdown.markdown(clean_text, True)
            st.session_state.chat_log.append({"name": "assistant", "msg": clean_text, "citations": citations})
            st.session_state.citations.extend(citations)
        except AttributeError as e:
            st.error(f"Error processing text: {e}")

    @override
    def on_tool_call_created(self, tool_call):
        st.session_state.current_tool_input = ""
        with st.chat_message("Assistant"):
            st.session_state.current_tool_input_markdown = st.empty()

    @override
    def on_tool_call_delta(self, delta, snapshot):
        if 'current_tool_input_markdown' not in st.session_state:
            with st.chat_message("Assistant"):
                st.session_state.current_tool_input_markdown = st.empty()

        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                st.session_state.current_tool_input += delta.code_interpreter.input
                input_code = f"### code interpreter\ninput:\n```python\n{st.session_state.current_tool_input}\n```"
                st.session_state.current_tool_input_markdown.markdown(input_code, True)

            if delta.code_interpreter.outputs:
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        pass

    @override
    def on_tool_call_done(self, tool_call):
        st.session_state.tool_calls.append(tool_call)
        if tool_call.type == "code_interpreter":
            input_code = f"### code interpreter\ninput:\n```python\n{tool_call.code_interpreter.input}\n```"
            st.session_state.current_tool_input_markdown.markdown(input_code, True)
            st.session_state.chat_log.append({"name": "assistant", "msg": input_code})
            st.session_state.current_tool_input_markdown = None
            for output in tool_call.code_interpreter.outputs:
                if output.type == "logs":
                    output = f"### code interpreter\noutput:\n```\n{output.logs}\n```"
                    with st.chat_message("Assistant"):
                        st.markdown(output, True)
                        st.session_state.chat_log.append({"name": "assistant", "msg": output})
