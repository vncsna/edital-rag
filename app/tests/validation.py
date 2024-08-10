from json import dump, load

from langchain.evaluation import load_evaluator

from app.main import WORKING_DIRECTORY, chain, retriever, vectorstore

REASONING_FILEPATH = WORKING_DIRECTORY / "data/reasoning.json"
EVALUATION_FILEPATH = WORKING_DIRECTORY / "data/evaluation.json"


def generate_data():
    """Generate evaluation data for validation"""

    if EVALUATION_FILEPATH.exists():
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

    with EVALUATION_FILEPATH.open("w") as file:
        dump(answers, file)


def validate_data():
    """Validate answers without references"""

    if REASONING_FILEPATH.exists():
        return

    with EVALUATION_FILEPATH.open("r") as file:
        data = load(file)

    evaluator = load_evaluator("score_string")

    evaluations = []
    for datum in data:
        evaluations.append(
            evaluator.evaluate_strings(
                input=datum["question"],
                prediction=datum["answer"],
            )
        )

    with REASONING_FILEPATH.open("w") as file:
        dump(evaluations, file)


generate_data()
validate_data()
