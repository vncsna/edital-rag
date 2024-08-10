from os import getenv
from pathlib import Path
from textwrap import dedent

import streamlit as st
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableBranch, RunnablePassthrough
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

    chat = ChatOpenAI(model_name=OPENAI_MODEL_NAME)

    # Summarize chat into a question to retrieve context

    query_transform_prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="messages"),
            (
                "user",
                "Dada a conversa acima, gere uma pergunta que deve obter "
                "informações relevantes para a conversa. Responda apenas com a pergunta.",
            ),
        ]
    )
    query_transforming_retriever_chain = RunnableBranch(
        (
            # Condition to check
            lambda x: len(x.get("messages", [])) == 1,
            # If only one message, then we just pass that message's content to retriever
            (lambda x: x["messages"][-1]["content"]) | retriever,
        ),
        # Else, then we pass inputs to LLM chain to transform the query, then pass to retriever
        query_transform_prompt | chat | StrOutputParser() | retriever,
    ).with_config(run_name="chat_retriever_chain")

    # Use the system template to answer the question

    template = dedent("""
        Voce e um assistente de atendimento que conversa sobre
        o edital do vestibular da unicamp em 2025 com jovens e adultos.
        Use apenas dados contidos no contexto para responder as questoes a seguir.

        <context>
        {context}
        </context>
    """)
    question_answering_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    document_chain = create_stuff_documents_chain(chat, question_answering_prompt)

    # Answer the last question with the chat and docs context

    conversational_retrieval_chain = (
        RunnablePassthrough
        .assign(context=query_transforming_retriever_chain)
        .assign(answer=document_chain)
    )  # fmt: skip

    return conversational_retrieval_chain, retriever


chain, retriever = generate_chain()


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
            response = chain.invoke({"messages": st.session_state.messages})
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
            print(f"DEBUG: {response}")
            st.rerun()


with tab2:
    value = DOCUMENT_FILEPATH.read_text()
    st.text_area(label="Edital 2025", label_visibility="collapsed", value=value, height=600)
