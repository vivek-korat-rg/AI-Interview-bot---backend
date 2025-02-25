import os
from dotenv import load_dotenv  # type: ignore
from crewai import Agent, LLM  # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import List

load_dotenv()

llm_4_mini = LLM(
    model="gpt-4o-mini", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY")
)


class Resume_Question(BaseModel):
    Question: str


class Resume_Question_List(BaseModel):
    Questions: List[Resume_Question]


resume_que_generator = Agent(
    role="Technical Question Generator",
    goal="Generate relevant, role-specific technical interview questions based on the candidate's resume and additional responses.",
    backstory="""You are a highly experienced technical interviewer specializing in generating tailored technical interview questions. 
    Your goal is to analyze the candidate’s resume and their detailed responses to create in-depth questions that assess:
    - Relevant technical knowledge for the specific role.
    - Problem-solving skills and coding abilities.
    - Practical application of tools, technologies, and concepts mentioned in their resume or response.
    You ensure that all questions are directly aligned with the requirements of the selected role, avoiding irrelevant topics.""",
    verbose=True,
    max_iter=5,
    llm=llm_4_mini,
)


class Question(BaseModel):
    Question: str
    Answer: str
    Rating: str
    Explanation: str


class Summary(BaseModel):
    Total_Score: str
    Percentage: str


class InterviewEvaluation(BaseModel):
    Questions: List[Question]
    Summary: Summary


follow_up_que_generator = Agent(
    role="Follow-up Question Generator",
    goal="Generate relevant follow-up technical interview questions based on the candidate's previous response and resume.",
    backstory="""You are an experienced technical interviewer. Your role is to create insightful and challenging follow-up 
    questions that delve deeper into the candidate’s technical knowledge, problem-solving abilities, and practical skills. 
    These questions are based on the candidate’s previous answers, ensuring a seamless progression in the interview while 
    probing further into areas that are critical to the role.""",
    verbose=True,
    max_iter=5,
    llm=llm_4_mini,
)

Answer_Evaluator = Agent(
    role="Answer Evaluator",
    goal="""Evaluate the provided answers based on relevance, clarity, accuracy, and completeness.""",
    backstory="""Your task is to assess each answer to the questions and assign a rating between 0 to 25, reflecting the quality and depth of the response.
            """,
    verbose=False,
    max_iter=3,
    llm=llm_4_mini,
)
