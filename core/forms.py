from django import forms
from .models import ContactMessage


class CropRecommendationForm(forms.Form):
    SOIL_CHOICES = [
        ("clay", "Clay"),
        ("sandy", "Sandy"),
        ("loamy", "Loamy"),
        ("silt", "Silt"),
        ("peat", "Peat"),
        ("chalk", "Chalk"),
    ]

    SEASON_CHOICES = [
        ("winter", "Winter"),
        ("summer", "Summer"),
        ("monsoon", "Monsoon"),
    ]

    RAINFALL_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    soil_type = forms.ChoiceField(choices=SOIL_CHOICES, label="Soil Type")
    season = forms.ChoiceField(choices=SEASON_CHOICES, label="Season")
    rainfall_level = forms.ChoiceField(choices=RAINFALL_CHOICES, label="Rainfall Level")



class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'border rounded px-4 py-3 w-full', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'border rounded px-4 py-3 w-full', 'placeholder': 'Email'}),
            'message': forms.Textarea(attrs={'class': 'border rounded px-4 py-3 w-full', 'rows': 5, 'placeholder': 'Message'}),
        }
        labels = {
            'name': 'Name',
            'email': 'Email',
            'message': 'Message',
        }
