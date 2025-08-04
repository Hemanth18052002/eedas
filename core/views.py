from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Job, Application


def index(request):
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'index.html', {'jobs': jobs})

def role_select(request):
    return render(request, 'select_role.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'partials/auth_modals.html', {'login_form': form})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('   ')
    else:
        form = UserCreationForm()
    return render(request, 'partials/auth_modals.html', {'register_form': form})

def logout_view(request):
    logout(request)
    return redirect('index')