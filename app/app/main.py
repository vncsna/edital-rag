from pathlib import Path

import streamlit as st

from app.utils import get_pdf_as_txt

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
