import bot.agents as Agents
from crewai import Crew, Task
import json
from .agents import InterviewEvaluation


class Evaluator:

    def __init__(self):

        self.pre_prompt = """Evaluation Criteria:
                Score Range: 0-25

                Key Factors:

                Relevance: The response must directly address the specific question with accuracy and focus.

                Responses that include only the question without meaningful content receive a score of 0.
                Responses that are irrelevant or overly elaborated but unrelated to the question also receive a score of 0.
                Uniqueness: Each response must provide unique and meaningful content.

                Repeating the same answer across multiple questions results in a score of 0 for all duplicate responses.
                Depth: The response should demonstrate understanding and provide sufficient detail.

                Answers should go beyond superficial explanations and show a thoughtful approach to solving the problem.
                Providing details such as key considerations, best practices, or potential challenges is encouraged, but examples are not mandatory unless explicitly requested in the question.
                Clarity: The explanation should be clear and concise.

                The response should be easy to understand and well-structured.

                Scoring Guidelines:

                Most Important Note :**The score is assigned dynamically within this range based on the response quality.**
                25: Perfect—deep insight, precise, and no gaps. The response fully addresses the question with clear, accurate, and well-rounded content. No further improvements needed.

                20-24: Excellent—highly detailed, accurate, and clear, but could be slightly refined in terms of specificity or completeness. The response is strong without needing examples, though examples would be helpful in some contexts.

                15-19: Good—covers the basics, but could benefit from more depth or clarity.
                
                10-14: Average—lacks clarity or depth, and may contain vague points.

                5-9: Below average—significant gaps, lacks important details or explanation.

                1-4: Poor—incomplete, unclear, or incorrect.

                0: Irrelevant, incorrect, duplicate, or no response.

                0 should be given if the response is irrelevant, vague, or duplicates an earlier answer, or if it is not a meaningful response.


                Important Notes:

                -> Scoring must not be restricted to multiples of 5. Scores should be awarded dynamically within the specified ranges (e.g., 18, 19, 22, etc.), based on the nuances and quality of the response.
                -> Scores should be assigned on a continuous scale within the ranges, with scores like 18, 19, 22, etc., representing the quality of the answer. The key is to match the score to the relevance, depth, and clarity of the response.
                -> 0 should be assigned for irrelevant, vague, or duplicate answers, or if the response contains no meaningful content.
                -> Examples should only be used if explicitly asked for. The quality of the response is evaluated based on how well it addresses the question, and examples should only enhance the response where necessary.

            """

    def Evaluation_of_ans(self, candidate_responses):

        Evaluation_task = Task(
            description=f"""
            Meticulously evaluate all candidate answers in {candidate_responses}.
            FOLLOW these evaluation guidelines:{self.pre_prompt}""",
            agent=Agents.Answer_Evaluator,
            expected_output="A JSON object with 'Questions' and 'Summary' fields.",
            output_json=InterviewEvaluation,
        )
        Evaluation_crew = Crew(
            agents=[Agents.Answer_Evaluator],
            tasks=[Evaluation_task],
        )

        self.Evaluations = Evaluation_crew.kickoff()
        self.Evaluations = parse_crew_output(self.Evaluations)

        return self.Evaluations


def parse_crew_output(crew_output):
    """
    Parse the CrewOutput object into a clean list of questions.
    """
    raw_data = getattr(crew_output, "raw", None)
    raw_data = json.loads(raw_data)

    return raw_data
