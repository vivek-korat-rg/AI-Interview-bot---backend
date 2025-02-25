from crewai import Crew, Task
import bot.agents as Agents
from .agents import Resume_Question_List
import json
import PyPDF2
from celery import shared_task
import json


Resume_Prompt_Instructions = """
    Objective:
    Generate a set of role-specific interview questions based on the skills, technologies, tools, and projects listed in the candidate’s resume, ensuring all aspects are relevant to the position they are interviewing for.

    Instructions:

    Skill Focus:

    Generate questions strictly based on the skills, technologies, tools, and projects relevant to the role the candidate is applying for.
    Avoid any skills, technologies, tools, or projects that are unrelated to the role in question.
    Uniqueness & Diversity:

    Ensure that each question explores a distinct aspect of the candidate's relevant skill set, avoiding repetition or overlap.
    Clarity & Precision:

    Questions should be clear and concise, with no more than 20 words, focusing on assessing fundamental understanding and practical problem-solving.
    Progressive Learning:

    Start with basic concepts and gradually increase the complexity of questions to evaluate the depth of knowledge in the relevant skills.
    Relevance to Candidates:

    Tailor questions for freshers or candidates with minimal industry experience, emphasizing academic knowledge and the ability to apply that knowledge practically.
    Scenario-Based & Practical:

    Ensure questions are based on real-world scenarios and practical application of the relevant skills. Avoid overly theoretical or production-level questions.
    Project Relevance:

    Exclude any projects listed on the resume that do not directly relate to the role the candidate is applying for. Focus on projects that showcase skills relevant to the position.
    """


class Interview_Qus_Generator:
    def __init__(self):
        pass

    def Resume_Questions(self, resume_path, selected_role, First_response):

        with open(resume_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            resume_content = ''

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]

                resume_content += page.extract_text()

            print(resume_content)
        question_task = Task(
            description=f"""
        Your objective is to generate precise, role-specific technical interview questions for a candidate based on their provided resume and additional response. Follow these steps:

        1. Analyze the candidate's resume for technical skills, projects, and technologies directly relevant to the role: {selected_role}.
        Resume: {resume_content}.

        2. Review the candidate's additional response for details on their hands-on experience, tools, and technologies used, challenges faced, and solutions implemented.
        Candidate Response: {First_response}.

         3. Focus on the **skills**, **projects**, and **tools/technologies** that align with the requirements of the {selected_role} role. Ensure a balanced evaluation across these aspects while ignoring irrelevant or unrelated details.

        4. Generate exactly 5 technical interview questions, adhering strictly to the following rules:
        - **3 questions must be based on the candidate's projects**, assessing their practical experience, problem-solving approaches, and challenges faced.
        - **2 questions must evaluate the candidate's skills and tools/technologies**, focusing on theoretical understanding and practical application.
        - Ensure the questions appear in **random order**, not grouped by type.

        5. Adhere strictly to the specified distribution (3 questions from projects and 2 from skills/tools/technologies). **Do not focus only on projects**—questions must strictly follow the rules above.

        6. Validate the output to confirm it contains 3 project-based questions and 2 skills/tools-based questions. If not, regenerate the output to meet the requirements.

        7. Avoid including general, non-technical, or HR-style questions. Ensure the questions are role-specific and tailored to the candidate's technical background.
        """,
            agent=Agents.resume_que_generator,
            expected_output="A JSON object with a 'Questions' field containing a list of questions.",
            output_json=Resume_Question_List,
        )

        question_crew = Crew(
            agents=[Agents.resume_que_generator],
            tasks=[question_task],
        )

        self.questions = question_crew.kickoff()
        return self.questions

    def Context_Question(self, context, selected_role):

        context_question = Task(
            description=f"""
            The candidate is interviewing for a {selected_role} role.
            Below are the candidate's responses to previously asked technical questions:
            {context}

            As an interviewer, your goal is to engage the candidate in a natural and in-depth conversation about the technical concepts discussed. Based on the candidate's answers, generate follow-up questions that reflect how an actual interview would progress. Each follow-up question should encourage the candidate to explain more about their thought process, delve deeper into specific topics, or provide real-world examples. The questions should flow smoothly from what the candidate has already said, simulating the interactive nature of a live interview.

            **Carefully read all questions and answers provided in the context file to fully understand the discussion and identify key themes, gaps, or opportunities for further exploration.**

            Here’s how to proceed:

            1. **Adjust for Relevance**: Prioritize follow-up questions based on your analysis of the candidate’s answers present in context that is provided:

                - **Case 1 (Highly Irrelevant or Almost Correct Answers)**: If an answer is highly irrelevant or almost correct, do **not generate follow-up questions**. Do not ask additional questions in this case.
                - **Case 2 (In-between Answers)**: For answers that fall between not almost right and highly irrelevant, generate **2 follow-up questions** for each response. Ensure that the total number of follow-up questions remains between **2 and 7**.
                - If there are no relevant follow-ups for **Case 2** answers, then you may refer back to **Case 1 topics** for follow-up questions as needed, ensuring the total number of questions does not exceed 7.

            **Validation Check**: Ensure that you are generating follow-up questions strictly for answers in **Case 2** (not highly irrelevant or almost correct), and the total number of follow-up questions must be between **2 and 7**. If this condition is not met, regenerate the output accordingly.


            2. **Natural Flow**: Generate follow-up questions that seamlessly continue the conversation and probe deeper into areas relevant to the {selected_role} role. Tailor the questions based on the candidate's previous answers:

                -For brief or unclear responses: Ask questions to encourage the candidate to elaborate on key points or clarify their statements.
                -For detailed but surface-level responses: Pose questions that push the candidate to explain how their knowledge applies to real-world scenarios or explore advanced concepts.
                -For comprehensive responses: Challenge the candidate with questions about edge cases, trade-offs, or potential improvements, encouraging critical thinking.

            3. **Role-Relevant Exploration**: Generate role-specific {selected_role} follow-up questions, probing unclear topics or missing areas, like unsupervised learning if only supervised was mentioned.

            4. **Tone and Context**: Generate conversational follow-up questions that smoothly build on the candidate's previous answers, avoiding abrupt transitions or jargon for a natural, engaging interview flow.

            5. **Topic Variety**: Ask maximum 2 questions on a topic, then shift to related areas or new aspects. Avoid revisiting topics to ensure diverse, well-rounded exploration.

            6.**Stay Contextually Relevant**: Focus on topics the candidate has already addressed, avoiding advanced or unrelated subjects. Keep questions beginner-friendly and relevant to their responses.
            Do Not mention the words or methods which candidate has not addressed or not mentioned.

            Rereminder :
            (Follow-up Questions Only):
            """,
            agent=Agents.follow_up_que_generator,
            expected_output="A JSON object with a 'Questions' field containing the follow-up questions.",
            output_json=Resume_Question_List,
        )

        context_question_crew = Crew(
            agents=[Agents.follow_up_que_generator],
            tasks=[context_question],
        )

        self.context_questions = context_question_crew.kickoff()
        return self.context_questions

    def parse_crew_output(self, crew_output):
        """_summary_

        Args:
            crew_output (_type_): _description_

        Returns:
            _type_: _description_
        """

        raw_data = getattr(crew_output, "raw", None)
        parsed_data = json.loads(raw_data)

        # Extract the list of questions
        questions_list = [q["Question"] for q in parsed_data["Questions"]]

        return questions_list
