
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings

from .models import StudentProfile, Job, JobApplication, RecruiterProfile


# ---------------- HOME ----------------

def home(request):
    jobs = Job.objects.all()
    return render(request, "core/home.html", {"jobs": jobs})


# ---------------- JOB MATCHES ----------------

def job_matches(request):
    profiles = StudentProfile.objects.all()
    jobs = Job.objects.all()
    results = []

    for profile in profiles:
        student_skills = {
            skill.strip().lower()
            for skill in (profile.skills or "").split(",")
            if skill.strip()
        }

        for job in jobs:
            required_skills = {
                skill.strip().lower()
                for skill in (job.required_skills or "").split(",")
                if skill.strip()
            }

            if not required_skills:
                continue

            matched_skills = student_skills & required_skills
            percentage = round(
                len(matched_skills) / len(required_skills) * 100
            )

            results.append({
                "student": profile,
                "job": job,
                "matched_skills": sorted(matched_skills),
                "percentage": percentage,
            })

    results.sort(key=lambda item: item["percentage"], reverse=True)

    return render(request, "core/job_matches.html", {"results": results})


# ---------------- STUDENT DASHBOARD ----------------

@login_required(login_url="login")
def student_dashboard(request):
    profile = StudentProfile.objects.filter(user=request.user).first()
    recommended_jobs = []
    applied_job_ids = set()

    if profile:
        student_skills = {
            skill.strip().lower()
            for skill in (profile.skills or "").split(",")
            if skill.strip()
        }

        applied_job_ids = set(
            JobApplication.objects.filter(
                student=profile
            ).values_list("job_id", flat=True)
        )

        for job in Job.objects.all():
            required_skills = {
                skill.strip().lower()
                for skill in (job.required_skills or "").split(",")
                if skill.strip()
            }

            if not required_skills:
                continue

            matched_skills = sorted(student_skills & required_skills)
            missing_skills = sorted(required_skills - student_skills)

            percentage = round(
                len(matched_skills) / len(required_skills) * 100
            )

            recommended_jobs.append({
                "job": job,
                "percentage": percentage,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            })

        recommended_jobs.sort(
            key=lambda item: item["percentage"],
            reverse=True,
        )

    return render(
        request,
        "core/dashboard.html",
        {
            "profile": profile,
            "recommended_jobs": recommended_jobs,
            "applied_job_ids": applied_job_ids,
        },
    )


# ---------------- STUDENT REGISTRATION ----------------

def register_student(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            StudentProfile.objects.create(
                user=user,
                full_name=request.POST.get("full_name", "").strip(),
                college=request.POST.get("college", "").strip(),
                skills=request.POST.get("skills", "").strip(),
            )

            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("student_dashboard")

        messages.error(request, "Please correct the registration errors.")
    else:
        form = UserCreationForm()

    return render(request, "core/register.html", {"form": form})


# ---------------- STUDENT LOGIN ----------------

def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            if RecruiterProfile.objects.filter(user=user).exists():
                messages.error(request, "Please use the recruiter login.")
                return redirect("recruiter_login")

            login(request, user)
            return redirect("student_dashboard")

        messages.error(request, "Invalid username or password.")

    return render(request, "core/login.html")


# ---------------- STUDENT LOGOUT ----------------

def student_logout(request):
    if request.method == "POST":
        logout(request)

    return redirect("home")


# ---------------- JOB SEARCH ----------------

@login_required(login_url="login")
def job_search(request):
    query = request.GET.get("q", "").strip()
    location = request.GET.get("location", "").strip()

    jobs = Job.objects.all().order_by("title")

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(company__icontains=query)
            | Q(required_skills__icontains=query)
        )

    if location:
        jobs = jobs.filter(location__icontains=location)

    profile = StudentProfile.objects.filter(user=request.user).first()
    applied_job_ids = set()

    if profile:
        applied_job_ids = set(
            JobApplication.objects.filter(
                student=profile
            ).values_list("job_id", flat=True)
        )

    return render(
        request,
        "core/job_search.html",
        {
            "jobs": jobs,
            "query": query,
            "location": location,
            "applied_job_ids": applied_job_ids,
        },
    )


# ---------------- APPLY FOR JOB ----------------

@login_required(login_url="login")
@require_POST
def apply_job(request, job_id):
    profile = StudentProfile.objects.filter(user=request.user).first()

    if profile is None:
        messages.error(request, "Please create your student profile first.")
        return redirect("student_dashboard")

    job = get_object_or_404(Job, id=job_id)

    application, created = JobApplication.objects.get_or_create(
        student=profile,
        job=job,
    )

    if created:
        messages.success(request, "You applied successfully!")
    else:
        messages.info(request, "You have already applied for this job.")

    return redirect("my_applications")


# ---------------- MY APPLICATIONS ----------------

@login_required(login_url="login")
def my_applications(request):
    profile = StudentProfile.objects.filter(user=request.user).first()
    applications = []

    if profile:
        applications = (
            JobApplication.objects.filter(student=profile)
            .select_related("job")
            .order_by("-applied_at")
        )

    return render(
        request,
        "core/my_applications.html",
        {"applications": applications},
    )


# ---------------- EDIT STUDENT PROFILE ----------------

@login_required(login_url="login")
def edit_profile(request):
    profile = StudentProfile.objects.filter(user=request.user).first()

    if profile is None:
        messages.error(request, "Student profile not found.")
        return redirect("student_dashboard")

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name", "").strip()
        profile.college = request.POST.get("college", "").strip()
        profile.degree = request.POST.get("degree", "BCA").strip()
        profile.skills = request.POST.get("skills", "").strip()

        resume = request.FILES.get("resume")
        if resume:
            profile.resume = resume

        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("student_dashboard")

    return render(
        request,
        "core/edit_profile.html",
        {"profile": profile},
    )


# ---------------- RECRUITER REGISTRATION ----------------

def recruiter_register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        company_name = request.POST.get("company_name", "").strip()
        phone = request.POST.get("phone", "").strip()

        if form.is_valid() and company_name:
            user = form.save()

            RecruiterProfile.objects.create(
                user=user,
                company_name=company_name,
                phone=phone,
            )

            messages.success(
                request,
                "Recruiter account created successfully. Please log in.",
            )
            return redirect("recruiter_login")

        if not company_name:
            messages.error(request, "Please enter your company name.")
        else:
            messages.error(request, "Please correct the registration errors.")
    else:
        form = UserCreationForm()

    return render(
        request,
        "core/recruiter_register.html",
        {"form": form},
    )


# ---------------- RECRUITER LOGIN ----------------

def recruiter_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None and RecruiterProfile.objects.filter(user=user).exists():
            login(request, user)
            return redirect("recruiter_dashboard")

        messages.error(request, "Invalid recruiter username or password.")

    return render(request, "core/recruiter_login.html")


# ---------------- RECRUITER DASHBOARD ----------------

@login_required(login_url="recruiter_login")
def recruiter_dashboard(request):
    profile = RecruiterProfile.objects.filter(user=request.user).first()

    if profile is None:
        messages.error(request, "Recruiter access only.")
        return redirect("recruiter_login")

    jobs = Job.objects.filter(recruiter=request.user).order_by("-id")

    return render(
        request,
        "core/recruiter_dashboard.html",
        {"profile": profile, "jobs": jobs},
    )


# ---------------- POST JOB ----------------

@login_required(login_url="recruiter_login")
def post_job(request):
    profile = RecruiterProfile.objects.filter(user=request.user).first()

    if profile is None:
        messages.error(request, "Recruiter access only.")
        return redirect("recruiter_login")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        required_skills = request.POST.get("required_skills", "").strip()
        location = request.POST.get("location", "").strip()
        salary = request.POST.get("salary", "").strip()
        description = request.POST.get("description", "").strip()

        if not all([title, required_skills, location, salary, description]):
            messages.error(request, "Please fill in every field.")
        else:
            Job.objects.create(
                title=title,
                company=profile.company_name,
                required_skills=required_skills,
                location=location,
                salary=salary,
                description=description,
                recruiter=request.user,
            )

            messages.success(request, "Job posted successfully!")
            return redirect("recruiter_dashboard")

    return render(
        request,
        "core/post_job.html",
        {"profile": profile},
    )


# ---------------- DELETE RECRUITER JOB ----------------

@login_required(login_url="recruiter_login")
@require_POST
def delete_recruiter_job(request, job_id):
    profile = RecruiterProfile.objects.filter(user=request.user).first()

    if profile is None:
        messages.error(request, "Recruiter access only.")
        return redirect("recruiter_login")

    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user,
    )

    job.delete()
    messages.success(request, "Your job listing was deleted.")
    return redirect("recruiter_dashboard")


# ---------------- RECRUITER LOGOUT ----------------

@login_required(login_url="recruiter_login")
@require_POST
def recruiter_logout(request):
    if not RecruiterProfile.objects.filter(user=request.user).exists():
        messages.error(request, "Recruiter access only.")
        logout(request)
        return redirect("recruiter_login")

    logout(request)
    return redirect("recruiter_login")


# ---------------- RECRUITER APPLICANTS ----------------

@login_required(login_url="recruiter_login")
def recruiter_applicants(request, job_id):
    profile = RecruiterProfile.objects.filter(user=request.user).first()

    if profile is None:
        messages.error(request, "Recruiter access only.")
        return redirect("recruiter_login")

    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user,
    )

    applications = (
        JobApplication.objects.filter(job=job)
        .select_related("student", "student__user")
        .order_by("-applied_at")
    )

    return render(
        request,
        "core/recruiter_applicants.html",
        {"job": job, "applications": applications},
    )


# ---------------- UPDATE APPLICATION STATUS ----------------

@login_required(login_url="recruiter_login")
@require_POST
def update_application_status(request, application_id):
    profile = RecruiterProfile.objects.filter(user=request.user).first()

    if profile is None:
        messages.error(request, "Recruiter access only.")
        return redirect("recruiter_login")

    application = get_object_or_404(
        JobApplication.objects.select_related(
            "job", "student", "student__user"
        ),
        id=application_id,
        job__recruiter=request.user,
    )

    new_status = request.POST.get("status", "").strip()

    if new_status not in ["Accepted", "Rejected", "Pending"]:
        messages.error(request, "Invalid application status.")
        return redirect(
            "recruiter_applicants",
            job_id=application.job_id,
        )

    application.status = new_status
    application.save(update_fields=["status"])

    student = application.student
    student_email = student.user.email

    if student_email:
        try:
            send_mail(
                subject=f"SkillBridge Application Update: {application.job.title}",
                message=(
                    f"Hello {student.full_name or student.user.username},\n\n"
                    f"Your application for {application.job.title} at "
                    f"{application.job.company} has been updated to: "
                    f"{new_status}.\n\n"
                    "Log in to SkillBridge to view your application status."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student_email],
                fail_silently=False,
            )
            messages.success(
                request,
                f"Application status updated to {new_status}. "
                "Email notification generated.",
            )
        except Exception:
            messages.warning(
                request,
                f"Application status updated to {new_status}, "
                "but the email notification failed.",
            )
    else:
        messages.success(
            request,
            f"Application status updated to {new_status}. "
            "The student has no email address registered.",
        )

    return redirect(
        "recruiter_applicants",
        job_id=application.job_id,
    )
