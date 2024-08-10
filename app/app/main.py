from pathlib import Path

import streamlit as st
from pypdf import PdfReader

########################################
# Helper


def get_pdf_as_txt(filepath: Path) -> str:
    filepath_txt = filepath.with_suffix(".txt")

    if filepath_txt.exists():
        return filepath_txt.read_text()

    reader = PdfReader(filepath)

    text = ""
    for page in reader.pages:
        text += page.extract_text()

    filepath_txt.write_text(text)

    return text


########################################
# App

st.title("Vestibular Unicamp")

tab1, tab2 = st.tabs(["Chat", "Referências"])

with tab1:
    with st.container(border=True, height=600):
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Load user input, process and return assistant output
        if prompt := st.chat_input("Digite uma dúvida"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": f"R: {prompt}"})
            st.rerun()


with tab2:
    filepath = Path(__file__).parent.parent.parent
    filepath = filepath / "data/EDITAL2025.pdf"

    value = get_pdf_as_txt(filepath)

    st.text_area(label="Edital 2025", label_visibility="collapsed", value=value, height=600)
