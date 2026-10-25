
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("job-matches/", views.job_matches, name="job_matches"),
    path("dashboard/", views.student_dashboard, name="student_dashboard"),
    path("register/", views.register_student, name="register"),
    path("login/", views.student_login, name="login"),
    path("logout/", views.student_logout, name="logout"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("apply/<int:job_id>/", views.apply_job, name="apply_job"),
    path("my-applications/", views.my_applications, name="my_applications"),

    path("search-jobs/", views.job_search, name="job_search"),

path(
    "recruiter/register/",
    views.recruiter_register,
    name="recruiter_register",
),
path(
    "recruiter/login/",
    views.recruiter_login,
    name="recruiter_login",
),

path(
    "recruiter/dashboard/",
    views.recruiter_dashboard,
    name="recruiter_dashboard",
),



path("recruiter/post-job/", views.post_job, name="post_job"),
path(
    "recruiter/delete-job/<int:job_id>/",
    views.delete_recruiter_job,
    name="delete_recruiter_job",
),
path("recruiter/logout/", views.recruiter_logout, name="recruiter_logout"),








path("recruiter/job/<int:job_id>/applicants/", views.recruiter_applicants, name="recruiter_applicants"),
path("recruiter/application/<int:application_id>/status/", views.update_application_status, name="update_application_status"),
]
