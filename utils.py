import streamlit as st

def generate_html_with_citations(chat_log):
    html_content = ""
    citation_details = ""
    for chat in chat_log:
        msg = chat["msg"]
        citations = chat.get("citations", [])
        for idx, citation in enumerate(citations):
            citation_text, citation_source = citation
            marker = f'<span style="color:blue; cursor:pointer;" onclick="showCitation({idx + 1})">[{idx + 1}]</span>'
            msg = msg.replace(citation_text, marker)
            citation_details += f'<div id="citation-{idx + 1}" style="display:none;">[{idx + 1}] {citation_source}</div>'
        html_content += f'<p>{msg}</p>'
    return html_content, citation_details

def add_tooltip_css():
    tooltip_css = """
    <style>
    .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        width: 250px;
        height: 100%;
        background-color: #f1f1f1;
        padding-top: 20px;
        overflow-x: hidden;
        transition: 0.5s;
        z-index: 1;
    }
    .sidebar a {
        padding: 10px 15px;
        text-decoration: none;
        font-size: 18px;
        color: #818181;
        display: block;
        transition: 0.3s;
    }
    .sidebar a:hover {
        color: #f1f1f1;
    }
    .main {
        margin-left: 260px;
        transition: margin-left 0.5s;
        padding: 20px;
    }
    </style>
    """
    st.markdown(tooltip_css, unsafe_allow_html=True)
