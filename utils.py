import streamlit as st

def generate_html_with_citations(chat_log):
    html_content = ""
    for chat in chat_log:
        msg = chat["msg"]
        citations = chat.get("citations", [])
        citation_texts = []
        for idx, citation in enumerate(citations):
            citation_text, citation_source = citation
            # Color the citation text within the message
            colored_citation = f'<span style="color:blue;">[{idx + 1}] {citation_text}</span>'
            msg = msg.replace(citation_text, colored_citation)
            citation_texts.append(f"[{idx + 1}] {citation_source}")
        if citation_texts:
            citation_details = "<br>".join(citation_texts)
            msg += f"""
                <details>
                  <summary>Citations</summary>
                  <p>{citation_details}</p>
                </details>
            """
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
