
from .tasks import Interview_Qus_Generator
from .evaluation import Evaluator
Eval = Evaluator()
Q_gen = Interview_Qus_Generator()


class Interviewer:
    def __init__(self):
        self.responses = []
        self.answer = []

    def Extract_user_lev(self, Evaluation):

        # Extracting and categorizing questions based on ratings
        below_average = []
        average = []
        good = []

        # Loop through each question in the JSON data
        for question in Evaluation["Questions"]:
            rating = int(
                question["Rating"].split("/")[0]
            )  # Extract the numeric part of the rating
            question_text = question["Question"]
            answer_text = question["Answer"]

            # Categorize based on the rating
            if rating < 8:
                below_average.append(
                    {"Question": question_text, "Answer": answer_text})
            elif 8 <= rating <= 20:
                average.append(
                    {"Question": question_text, "Answer": answer_text})
            else:
                good.append({"Question": question_text, "Answer": answer_text})

        return below_average, average, good

    def lvl_evaluation(self, responses, selected_role):

        print("full_response", responses)

        Evaluation = Eval.Evaluation_of_ans(responses)
        print("Evaluation", Evaluation)
        below_average, average, good = self.Extract_user_lev(Evaluation)

        if average:
            number_of_questions = len(Evaluation["Questions"])
            total_score = Evaluation['Summary']['Total_Score']
            context_questions = Q_gen.Context_Question(average, selected_role)
            return context_questions, total_score, number_of_questions
        return None
