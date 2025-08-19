from django.contrib import admin
from .models import SchoolProfile

@admin.register(SchoolProfile)
class SchoolProfileAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'school_type', 'school_status')
