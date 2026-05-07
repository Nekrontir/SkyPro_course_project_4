from django import forms
from .models import MailingRecipient

class RecipientForm(forms.ModelForm):
    class Meta:
        model = MailingRecipient
        fields = ['email', 'full_name', 'comment']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }