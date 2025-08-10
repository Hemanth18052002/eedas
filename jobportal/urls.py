from django.contrib import admin
from django.urls import path
from core import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('verify-otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('resend-otp/<int:user_id>/', views.resend_otp, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('create-job/', views.create_job, name='create_job'),
    path('edit-job/<int:job_id>/', views.edit_job, name='edit_job'),
    path('apply-job/<int:job_id>/', views.apply_job, name='apply_job'),
    path('applicants/<int:job_id>/', views.applicants, name='applicants'),
    path('test-db/', views.test_db, name='test_db'),
    path('test-email/', views.test_email, name='test_email'),
]

urlpatterns += staticfiles_urlpatterns()
