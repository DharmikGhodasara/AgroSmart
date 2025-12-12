from django.db import models

# Create your models here.


class Tip(models.Model):
    CATEGORY_CHOICES = [
        ("soil", "Soil & Nutrients"),
        ("watering", "Watering & Irrigation"),
        ("pest", "Pest & Disease"),
        ("harvest", "Harvest & Storage"),
        ("general", "General"),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to="tips/", blank=True, null=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="general")
    crop = models.CharField(max_length=100, blank=True, help_text="Optional crop name for filtering")
    season = models.CharField(max_length=50, blank=True, help_text="Optional season for filtering")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} <{self.email}>"
