from celery import shared_task
from .question_generation import Interview_Qus_Generator
from .models import *
from .interview_session import Interviewer
from .evaluation import Evaluator
from .models import CandidateScore
import json


@shared_task
def generate_resume_questions(resume_path, selected_role, first_response, candidate_id):
    job_role = JobRole.objects.get(name=selected_role)
    candidate = Candidate.objects.get(id=candidate_id)
    existing_questions = Question.objects.filter(
        job_role=job_role, candidate=candidate, question_type=Question.RESUME_BASED
    )

    if existing_questions.exists():
        print("EXISTING QUESTIONS")
        print(existing_questions)
        return existing_questions

    obj = Interview_Qus_Generator()
    print(resume_path, selected_role, first_response)
    questions = obj.Resume_Questions(resume_path=resume_path,
                                     selected_role=selected_role, First_response=first_response)

    print("QUESTIONSSSSSSSSSSSSSSSSS")
    print(questions)
    for question in questions['Questions']:
        Question.objects.create(
            job_role=job_role,
            question_type=Question.RESUME_BASED,
            text=question['Question'],
            candidate=candidate
        )

    return questions


@shared_task
def generate_follow_up_questions(context, selected_role, candidate_id):
    job_role = JobRole.objects.get(name=selected_role)
    candidate = Candidate.objects.get(id=candidate_id)

    existing_questions = Question.objects.filter(
        job_role=job_role, candidate=candidate, question_type=Question.FOLLOW_UP
    )
    if existing_questions.exists():
        existing_questions.delete()
        
    interviewer = Interviewer()
    questions, role_based_score, number_of_questions = interviewer.lvl_evaluation(
        context, selected_role
    )

    role_based_score = (float(role_based_score) * 100) / \
        (int(number_of_questions) * 25)
    CandidateScore.objects.update_or_create(
        candidate=candidate, role_based_score=role_based_score)

    if not questions:
        print("No follow-up questions needed (Candidate is either too strong or too weak).")
        return None

    print("Generated Follow-Up Questions:")
    for question in questions['Questions']:
        Question.objects.create(
            job_role=job_role,
            question_type=Question.FOLLOW_UP,
            text=question['Question'],
            candidate=candidate
        )

    return questions


@shared_task
def evaluate_answers(context):
    evaluator = Evaluator()
    evaluation = evaluator.Evaluation_of_ans(context)
    print("EVALUATION", evaluation)

    return evaluation
