from django.contrib import admin

from .models import Message, UserProfile


@admin.register(UserProfile)
class UserProfile(admin.ModelAdmin):
    list_display = ("user", "is_manager")
    search_fields = ("is_manager",)


@admin.register(Message)
class Message(admin.ModelAdmin):
    list_display = ("topic", "created_at", "owner")
