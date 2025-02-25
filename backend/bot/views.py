from .models import *
from .serializers import CandidateSerializer, QuestionSerializer, AnswerSerializer, JobRoleSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from .tasks import generate_resume_questions, generate_follow_up_questions, evaluate_answers
import logging

logger = logging.getLogger(__name__)


class JobRoleView(APIView):
    def get(self, request):
        try:
            job_roles = JobRoleSerializer(JobRole.objects.all(), many=True)
            return Response({"job_roles": job_roles.data})
        except Exception as e:
            logger.error(f"Internal Server Error: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CandidateView(APIView):
    def get(self, request):
        try:
            candidates = Candidate.objects.all()
            serialized_candidates = CandidateSerializer(candidates, many=True)
            return Response({"candidates": serialized_candidates.data})
        except Exception as e:
            logger.error(f"Internal Server Error: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = CandidateSerializer(data=request.data)
            if serializer.is_valid():
                candidate = serializer.save()
                return Response(
                    {"message": "Candidate created", "candidate": serializer.data},
                    status=status.HTTP_201_CREATED,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Internal Server Error: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RoleBasedQuestionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, role):
        print(role)
        try:
            if not role:
                return Response({"message": "Role is required"}, status=status.HTTP_400_BAD_REQUEST)
            job_name = JobRole.objects.get(id=role)
            print(job_name)
            role = JobRole.objects.get(name=job_name)
            easy_questions = Question.objects.filter(
                job_role=role, question_type=Question.ROLE_BASED, tags="easy"
            ).order_by("?")[:2]

            hard_questions = Question.objects.filter(
                job_role=role, question_type=Question.ROLE_BASED, tags="intermediate"
            ).order_by("?")[:2]

            questions = list(easy_questions) + list(hard_questions)

            if not questions:
                return Response({"message": "No questions found for the given role"}, status=status.HTTP_404_NOT_FOUND)

            serialized_questions = QuestionSerializer(questions, many=True)
            return Response({"questions": serialized_questions.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Internal Server Error: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeBasedQuestionView(APIView):
    def get(self, request, candidate_id):
        try:
            if not candidate_id:
                return Response({"message": "Candidate ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                candidate = Candidate.objects.get(id=candidate_id)
            except Candidate.DoesNotExist:
                raise NotFound("Candidate not found")

            questions = Question.objects.filter(
                question_type=Question.RESUME_BASED, candidate=candidate
            )

            if not questions:
                return Response({"message": "No resume-based questions found for the candidate"}, status=status.HTTP_404_NOT_FOUND)

            serialized_questions = QuestionSerializer(questions, many=True)
            return Response({"questions": serialized_questions.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Internal Server Error: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FollowUpQuestionView(APIView):
    def get(self, request, candidate_id):
        try:
            if not candidate_id:
                return Response({"error": "Candidate ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                candidate = Candidate.objects.get(id=candidate_id)
            except Candidate.DoesNotExist:
                raise NotFound("Candidate not found")

            questions = Question.objects.filter(
                question_type=Question.FOLLOW_UP, candidate=candidate
            )

            if not questions:
                return Response({"message": "No follow-up questions found for the candidate"}, status=status.HTTP_404_NOT_FOUND)

            serialized_questions = QuestionSerializer(questions, many=True)
            return Response({"questions": serialized_questions.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Internal Server Error: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubmitAnswer(APIView):
    def post(self, request):
        try:
            first_question_ans = request.data.get("first_question_ans")
            candidate_id = request.data.get("candidate_id")

            if first_question_ans:
                try:
                    candidate = Candidate.objects.get(id=candidate_id)
                except Candidate.DoesNotExist:
                    return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)

                resume = candidate.resume.path
                job_role = candidate.job_role.name

                generate_resume_questions.delay(
                    resume, job_role, first_question_ans, candidate_id)

                return Response({"message": "Resume-based questions are being generated"}, status=status.HTTP_200_OK)

            serializer = AnswerSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Answer submitted"}, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Internal Server Error: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateFollowUpQuestions(APIView):
    def post(self, request):
        try:
            candidate_id = request.data.get("candidate_id")

            if not candidate_id:
                return Response({"error": "Candidate ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                candidate = Candidate.objects.get(id=candidate_id)
            except Candidate.DoesNotExist:
                return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)

            job_role = candidate.job_role.name

            follow_up_questions = Question.objects.filter(
                question_type=Question.FOLLOW_UP, candidate=candidate
            )
            if follow_up_questions.exists():
                return Response({"message": "Follow-up questions already generated"}, status=status.HTTP_200_OK)

            context = request.data.get("context")
            if not context:
                return Response({"error": "Context is required"}, status=status.HTTP_400_BAD_REQUEST)

            generate_follow_up_questions.delay(context, job_role, candidate_id)

            return Response({"message": "Follow-up questions generated"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Internal Server Error: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EvaluateScore(APIView):
    def get(self, request, candidate_id):
        try:
            if not candidate_id:
                return Response({"error": "Candidate ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                candidate = Candidate.objects.get(id=candidate_id)
            except Candidate.DoesNotExist:
                return Response({"error": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)

            context = request.data.get("context")
            if not context:
                return Response({"error": "Context is required"}, status=status.HTTP_400_BAD_REQUEST)

            evaluation = evaluate_answers(context)
            total_evaluation_score = evaluation['Summary']['Total_Score']
            total_evaluation_score = (
                float(total_evaluation_score) * 100) / (float(len(context['questions'])) * 25)

            candidate_score, created = CandidateScore.objects.update_or_create(
                candidate=candidate,
                defaults={"total_evaluation_score": total_evaluation_score}
            )
            candidate_score.update_overall_score()

            candidate_score = CandidateScore.objects.get(candidate=candidate)
            return Response({"score": candidate_score.total_evaluation_score}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Internal Server Error: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
