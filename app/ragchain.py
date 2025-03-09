import os
from operator import itemgetter
from typing import TypedDict

from dotenv import load_dotenv
from langchain.vectorstores import PGVector
from langchain.prompts import ChatPromptTemplate
from langchain.chains import RunnableParallel
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from app.config import PG_COLLECTION_NAME

load_dotenv()

vector_store = PGVector(
    collection_name=PG_COLLECTION_NAME,
    connection_string=os.getenv("POSTGRES_URL"),
    embedding_function=OpenAIEmbeddings(model='text-embedding-ada-002')
)

template = """
Answer given the following context:
{context}

Question: {question}
"""

ANSWER_PROMPT = ChatPromptTemplate.from_template(template)

llm = ChatOpenAI(temperature=0, model='gpt-4-1106-preview', streaming=True)


class RagInput(TypedDict):
    question: str


final_chain = (
        RunnableParallel(
            context=(itemgetter("question") | vector_store.as_retriever()),
            question=itemgetter("question")
        ) |
        RunnableParallel(
            answer=(ANSWER_PROMPT | llm),
            docs=itemgetter("context")
        )

).with_types(input_type=RagInput)
