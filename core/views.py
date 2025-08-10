from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from .models import Job, Application, UserProfile, CustomUser
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ApplicationForm
import random

def index(request):
    user_profile = None
    if request.user.is_authenticated:
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if user_profile.role == 'company':
            jobs = Job.objects.filter(employer=request.user).order_by('-created_at')
        else:
            jobs = Job.objects.all().order_by('-created_at')
    else:
        jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'index.html', {'jobs': jobs, 'user_profile': user_profile})

def generate_otp():
    return str(random.randint(100000, 999999))

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                user_profile, created = UserProfile.objects.get_or_create(user=user)
                user_profile.role = form.cleaned_data['role']
                otp = generate_otp()
                user_profile.otp = otp
                user_profile.save()
                
                try:
                    send_mail(
                        'Verify Your EEDAS Job Portal Account',
                        f'Your OTP for account verification is: {otp}',
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    messages.success(request, 'Registration successful! Please check your email for the OTP to verify your account.')
                    return redirect('verify_otp', user_id=user.id)
                except Exception as e:
                    messages.error(request, f'Failed to send OTP email: {str(e)}. Please try again.')
                    user.delete()
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}. Please try again.')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'register_form': form})

def verify_otp(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        user_profile = UserProfile.objects.get(user=user)
        if request.method == 'POST':
            otp = request.POST.get('otp')
            if otp == user_profile.otp:
                user.is_active = True
                user.save()
                user_profile.is_verified = True
                user_profile.otp = None
                user_profile.save()
                login(request, user)
                messages.success(request, 'Account verified and activated!')
                return redirect('index')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
        return render(request, 'verify_otp.html', {'user_id': user_id})
    except CustomUser.DoesNotExist:
        messages.error(request, 'User does not exist.')
        return redirect('signup')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('signup')

def resend_otp(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        user_profile = UserProfile.objects.get(user=user)
        otp = generate_otp()
        user_profile.otp = otp
        user_profile.save()
        try:
            send_mail(
                'Resend OTP for EEDAS Job Portal',
                f'Your new OTP for account verification is: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'A new OTP has been sent to your email.')
        except Exception as e:
            messages.error(request, f'Failed to resend OTP: {str(e)}. Please try again.')
        return redirect('verify_otp', user_id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, 'User does not exist.')
        return redirect('signup')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('signup')

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                messages.error(request, 'Your account is not verified. Please verify using the OTP sent to your email.')
                return redirect('resend_otp', user_id=user.id)
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid credentials. Please try again.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'login_form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html', {'user': request.user, 'user_profile': user_profile})

def create_job(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if user_profile.role != 'company':
        messages.error(request, 'Only companies can create jobs.')
        return redirect('index')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        company = request.POST.get('company')
        location = request.POST.get('location')
        description = request.POST.get('description')
        try:
            Job.objects.create(
                title=title,
                company=company,
                location=location,
                description=description,
                employer=request.user
            )
            messages.success(request, 'Job created successfully!')
            return redirect('index')
        except Exception as e:
            messages.error(request, f'Failed to create job: {str(e)}')
    
    return render(request, 'create_job.html')

def edit_job(request, job_id):
    if not request.user.is_authenticated:
        return redirect('login')
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if user_profile.role != 'company':
        messages.error(request, 'Only companies can edit jobs.')
        return redirect('index')
    
    job = get_object_or_404(Job, id=job_id, employer=request.user)
    
    if request.method == 'POST':
        job.title = request.POST.get('title')
        job.company = request.POST.get('company')
        job.location = request.POST.get('location')
        job.description = request.POST.get('description')
        try:
            job.save()
            messages.success(request, 'Job updated successfully!')
            return redirect('index')
        except Exception as e:
            messages.error(request, f'Failed to update job: {str(e)}')
    
    return render(request, 'edit_job.html', {'job': job})

def apply_job(request, job_id):
    if not request.user.is_authenticated:
        return redirect('login')
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if user_profile.role != 'student':
        messages.error(request, 'Only students can apply for jobs.')
        return redirect('index')
    
    job = get_object_or_404(Job, id=job_id)
    if Application.objects.filter(user=request.user, job=job).exists():
        messages.error(request, 'You have already applied for this job.')
        return redirect('index')
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            try:
                application = form.save(commit=False)
                application.user = request.user
                application.job = job
                application.save()
                messages.success(request, 'Application submitted successfully!')
                return redirect('index')
            except Exception as e:
                messages.error(request, f'Failed to submit application: {str(e)}')
        else:
            messages.error(request, 'Application failed. Please correct the errors below.')
    else:
        form = ApplicationForm(initial={'email': request.user.email})
    
    return render(request, 'apply_job.html', {'form': form, 'job': job})

def applicants(request, job_id):
    if not request.user.is_authenticated:
        return redirect('login')
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if user_profile.role != 'company':
        messages.error(request, 'Only companies can view applicants.')
        return redirect('index')
    
    job = get_object_or_404(Job, id=job_id, employer=request.user)
    applications = Application.objects.filter(job=job)
    
    return render(request, 'applicants.html', {'job': job, 'applications': applications})

def test_db(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return HttpResponse("Database connection successful!")
    except Exception as e:
        return HttpResponse(f"Database connection failed: {str(e)}")

def test_email(request):
    try:
        send_mail(
            'Test Email',
            'This is a test email from EEDAS Job Portal.',
            settings.DEFAULT_FROM_EMAIL,
            ['test@example.com'],
            fail_silently=False,
        )
        messages.success(request, 'Test email sent successfully!')
    except Exception as e:
        messages.error(request, f'Failed to send test email: {str(e)}')
    return redirect('index')