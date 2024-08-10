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

st.title("Vestibular Unicamp 2025")

tab1, tab2 = st.tabs(["Dúvidas", "Referências"])

with tab1:
    user_input = st.text_input("Qual a sua dúvida sobre o edital?")

    if st.button("Perguntar"):
        if user_input:
            st.write(user_input)
        else:
            st.write("Por favor adicione uma dúvida")


with tab2:
    filepath = Path(__file__).parent.parent.parent
    filepath = filepath / "data/EDITAL2025.pdf"

    value = get_pdf_as_txt(filepath)

    st.text_area(label="Edital 2025", value=value, height=600)
