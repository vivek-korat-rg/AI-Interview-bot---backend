from .views import *
from django.urls import path

urlpatterns = [
    path('job_roles/', JobRoleView.as_view(), name='job_roles'),
    path('create_candidate/', CandidateView.as_view(), name='create_candidate'),
    path('role_based_questions/<int:role>/', RoleBasedQuestionView.as_view(),
         name='role_based_questions'),
    path('resume_based_questions/<int:candidate_id>/',
         ResumeBasedQuestionView.as_view(), name='resume_based_questions'),
    path('follow_up_questions/<int:candidate_id>/', FollowUpQuestionView.as_view(),
         name='follow_up_questions'),
    path('submit_answer/', SubmitAnswer.as_view(), name='submit_answer'),
    path('generate_follow_up_questions/', GenerateFollowUpQuestions.as_view(),
         name='generate_follow_up_questions'),
    path('evaluate_score/<int:candidate_id>',
         EvaluateScore.as_view(), name='evaluate_score'),
]
