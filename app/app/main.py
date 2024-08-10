from os import getenv
from pathlib import Path

import streamlit as st
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from pypdf import PdfReader

OPENAI_API_KEY = getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = getenv("OPENAI_MODEL_NAME")

LANGCHAIN_CHUNK_SIZE_CHILD = int(getenv("LANGCHAIN_CHUNK_SIZE_CHILD"))
LANGCHAIN_CHUNK_SIZE_PARENT = int(getenv("LANGCHAIN_CHUNK_SIZE_PARENT"))
LANGCHAIN_MODEL_NAME = getenv("LANGCHAIN_MODEL_NAME")

WORKING_DIRECTORY = Path(__file__).parents[2]
DOCUMENT_FILEPATH = WORKING_DIRECTORY / "data/EDITAL2025.txt"
EMBEDDINGS_DIRECTORY = str(WORKING_DIRECTORY / "data/embeddings")

########################################
# Helper


def save_pdf_as_txt(filepath: Path):
    filepath_txt = filepath.with_suffix(".txt")

    if not filepath_txt.exists():
        reader = PdfReader(filepath)

        text = ""
        for page in reader.pages:
            text += page.extract_text()

        filepath_txt.write_text(text)


########################################
# LLM


def generate_chain():
    """Setup retrieval chain and return caller"""

    documents = TextLoader(DOCUMENT_FILEPATH).load()

    embedding = HuggingFaceEmbeddings(model_name=LANGCHAIN_MODEL_NAME)

    docstore = InMemoryStore()

    vectorstore = Chroma(
        collection_name="split_parents",
        embedding_function=embedding,
        persist_directory=EMBEDDINGS_DIRECTORY,
    )

    child_splitter = RecursiveCharacterTextSplitter(chunk_size=LANGCHAIN_CHUNK_SIZE_CHILD)
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=LANGCHAIN_CHUNK_SIZE_PARENT)

    retriever = ParentDocumentRetriever(
        docstore=docstore,
        vectorstore=vectorstore,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )
    retriever.add_documents(documents)

    llm = ChatOpenAI(model_name=OPENAI_MODEL_NAME)

    template = """
    Voce e um assistente de atendimento que conversa sobre
    o edital do vestibular da unicamp em 2025 com jovens e adultos.
    Use apenas dados contidos no contexto para responder as questoes a seguir.

    <context>
    {context}
    </context>

    Questao: {input}
    """
    prompt = ChatPromptTemplate.from_template(template)

    documents_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, documents_chain)

    return retrieval_chain


chain = generate_chain()


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
            response = chain.invoke({"input": prompt})
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
            st.rerun()


with tab2:
    value = DOCUMENT_FILEPATH.read_text()
    st.text_area(label="Edital 2025", label_visibility="collapsed", value=value, height=600)
