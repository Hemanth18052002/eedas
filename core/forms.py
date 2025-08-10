from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Application

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Enter a valid email address.")
    role = forms.ChoiceField(
        choices=[('student', 'Student'), ('company', 'Company')],
        required=True,
        help_text="Select your role."
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2', 'role')

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", help_text="Enter your email address.")

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['full_name', 'phone_number', 'linkedin_link', 'resume_link']
        widgets = {
            'linkedin_link': forms.URLInput(attrs={'placeholder': 'https://www.linkedin.com/in/your-profile'}),
            'resume_link': forms.URLInput(attrs={'placeholder': 'https://drive.google.com/your-resume'}),
        }