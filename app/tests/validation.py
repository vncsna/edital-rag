from json import dump

from app.main import WORKING_DIRECTORY, chain, retriever, vectorstore

CONTEXT_FILEPATH = WORKING_DIRECTORY / "data/evaluation.json"


def generate_data():
    """Generate evaluation data for validation"""

    if CONTEXT_FILEPATH.exists():
        return

    answers = []
    for question in [
        "Quantas vagas foram oferecidas?",  # PG01
        "Quem pode se inscrever no vestibular?",  # PG02
        "Quando são as inscrições pro vestibular?",  # PG05
        "Que tipos de isenções existem ",  # PG05
        "Quais são os documentos necessários para matricula?",  # PG12
        "Como é a prova no primeiro dia?",  # PG21
        "Como é a prova no segundo dia?",  # PG22
        "Qual o conteudo da prova de língua portuguesa?",  # PG25
        "Qual é o conjunto de habilidades exigidas de matemática?",  # PG27
        "Como estão divididas as provas de habilidades específicas para história da arte?",  # PG49
    ]:
        messages = [
            {
                "role": "user",
                "content": question,
            }
        ]
        answers.append(
            {
                "question": question,
                "answer": chain.invoke({"messages": messages})["answer"],
                "context_by_invoke": [
                    document.page_content for document in retriever.invoke(question)
                ],
                "context_by_similarity": [
                    document.page_content for document in vectorstore.similarity_search(question)
                ],
            }
        )
    with CONTEXT_FILEPATH.open("w") as file:
        dump(answers, file)


generate_data()

