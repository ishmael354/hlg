import streamlit as st

def generate_html_with_tooltips(chat_log):
    html_content = ""
    for chat in chat_log:
        msg = chat["msg"]
        citations = chat.get("citations", [])
        for citation in citations:
            citation_text, citation_source = citation
            tooltip = f'<span class="tooltip">{citation_text}<span class="tooltiptext">{citation_source}</span></span>'
            msg = msg.replace(citation_text, tooltip)
        html_content += f'<p>{msg}</p>'
    return html_content

def add_tooltip_css():
    tooltip_css = """
    <style>
    .tooltip {
      position: relative;
      display: inline-block;
      cursor: pointer;
      border-bottom: 1px dotted black;
    }

    .tooltip .tooltiptext {
      visibility: hidden;
      width: 120px;
      background-color: black;
      color: #fff;
      text-align: center;
      border-radius: 6px;
      padding: 5px 0;
      position: absolute;
      z-index: 1;
      bottom: 125%; /* Position the tooltip above the text */
      left: 50%;
      margin-left: -60px;
      opacity: 0;
      transition: opacity 0.3s;
    }

    .tooltip:hover .tooltiptext {
      visibility: visible;
      opacity: 1;
    }
    </style>
    """
    st.markdown(tooltip_css, unsafe_allow_html=True)
