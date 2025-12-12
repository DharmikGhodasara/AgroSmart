from django.contrib import admin
from .models import Tip, ContactMessage

@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "crop", "season", "created_at")
    list_filter = ("category", "season", "created_at")
    search_fields = ("title", "content", "crop")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("created_at",)
