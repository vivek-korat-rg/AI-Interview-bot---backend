from django.db import models


class JobRole(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Candidate(models.Model):
    resume = models.FileField(upload_to="resumes/")
    job_role = models.ForeignKey(JobRole, on_delete=models.SET_NULL, null=True)
    overall_score = models.FloatField(default=0.0)  # Store final score

    def __str__(self):
        return f"Candidate {self.id} - {self.job_role.name if self.job_role else 'No Role'}"


class Question(models.Model):
    ROLE_BASED = "role"
    RESUME_BASED = "resume"
    FOLLOW_UP = "follow_up"

    QUESTION_TYPES = [
        (ROLE_BASED, "Role-Based"),
        (RESUME_BASED, "Resume-Based"),
        (FOLLOW_UP, "Follow-Up"),
    ]

    job_role = models.ForeignKey(
        JobRole, on_delete=models.CASCADE, null=True, blank=True
    )
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, null=True, blank=True
    )
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPES
    )
    text = models.TextField()
    tags = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.get_question_type_display()} - {self.text[:50]}"


class Answer(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    score = models.FloatField(default=0.0)  # Store score for each answer
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.id} - {self.question.text[:30]}"


class CandidateScore(models.Model):
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE)
    role_based_score = models.FloatField(default=0.0)
    total_evaluation_score = models.FloatField(default=0.0)

    def update_overall_score(self):
        self.candidate.overall_score = (
            float(self.role_based_score) + float(self.total_evaluation_score)
        )/2
        self.candidate.save()

    def __str__(self):
        return f"Scores for {self.candidate.id}"
