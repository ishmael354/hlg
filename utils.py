import pandas as pd

def generate_html_with_citations(chat_log):
    html_content = ""
    for chat in chat_log:
        html_content += f"<div><strong>{chat['name']}:</strong> {chat['msg']}</div>"
    return html_content

def add_tooltip_css():
    pass  # No-op for now as we removed the citations
