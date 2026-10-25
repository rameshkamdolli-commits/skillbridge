
from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )
    full_name = models.CharField(max_length=150, blank=True)
    college = models.CharField(max_length=200, blank=True)
    degree = models.CharField(max_length=100, default="BCA")
    skills = models.TextField(blank=True)
    resume = models.FileField(
        upload_to="resumes/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.full_name or self.user.username


class Job(models.Model):
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posted_jobs"
    )
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    required_skills = models.TextField()
    location = models.CharField(max_length=200)
    salary = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.title} at {self.company}"


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Accepted", "Accepted"),
        ("Rejected", "Rejected"),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "job"],
                name="unique_student_job_application"
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.job.title} ({self.status})"


class RecruiterProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter_profile"
    )
    company_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.company_name} - {self.user.username}"
