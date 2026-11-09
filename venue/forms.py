from django import forms
from django.utils import timezone

from .models import BookingRequest


class BookingForm(forms.ModelForm):
    class Meta:
        model = BookingRequest
        fields = ["name", "phone", "date", "guests", "hall", "event_format", "comment"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Как к вам обращаться", "autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"placeholder": "+7 (___) ___-__-__", "autocomplete": "tel", "type": "tel"}),
            "date": forms.DateInput(attrs={"type": "date"}),
            "guests": forms.NumberInput(attrs={"min": 1, "max": 350, "placeholder": "50"}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Пожелания, тайминг, вопросы"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hall"].empty_label = "Пока не выбрал"
        self.fields["event_format"].empty_label = "Другое"
        # Не даём выбрать прошедшую дату прямо в календаре браузера
        self.fields["date"].widget.attrs["min"] = timezone.localdate().isoformat()

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date < timezone.localdate():
            raise forms.ValidationError("Машину времени пока не завезли — выберите дату в будущем.")
        return date
