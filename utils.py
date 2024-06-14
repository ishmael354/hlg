import streamlit as st

def generate_html_with_tooltips(chat_log):
    html_content = ""
    for chat in chat_log:
        if chat["name"] == "assistant" and chat["citations"]:
            msg_with_tooltips = chat["msg"]
            for citation, source_text in chat["citations"]:
                msg_with_tooltips = msg_with_tooltips.replace(
                    citation,
                    f'<span class="tooltip">{citation}<span class="tooltiptext">{source_text}</span></span>'
                )
            html_content += f'<div class="chat-message assistant">{msg_with_tooltips}</div>'
        else:
            html_content += f'<div class="chat-message {chat["name"]}">{chat["msg"]}</div>'
    return html_content

def add_tooltip_css():
    css_file_path = "static/styles.css"
    try:
        with open(css_file_path) as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading CSS file: {e}")
