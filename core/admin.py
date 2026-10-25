
from django.contrib import admin
from .models import StudentProfile, Job, JobApplication

class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "college", "degree", "user")
    search_fields = ("full_name", "college", "user__username")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location")
    search_fields = ("title", "company")


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("student", "job", "status", "applied_at")
    list_filter = ("status", "applied_at")
    search_fields = ("student__full_name", "job__title", "job__company")
