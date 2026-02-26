# mainapp/urls.py → FINAL PERFECT VERSION (NO MORE 404s EVER)

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ======================== MAIN PAGES ========================

    path("", views.welcome, name="welcome"),
    path("home/", views.home, name="home"),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('search/', views.search, name='search'),

    # ======================== CROPS ========================
    path('crops/', views.crop_list, name='crops_list'),
    path('crops/my/', views.my_crops, name='my_crops'),
    path('crops/add/', views.add_crop, name='add_crop'),
    path('edit-crop/<int:pk>/', views.edit_crop, name='edit_crop'),
    path('delete-crop/<int:pk>/', views.delete_crop, name='delete_crop'),
    path('my-crops/', views.my_crops, name='my_crops'),
    # ======================== TOOLS ========================
    path('tools/', views.tool_list, name='tools_list'),
    path('tools/add/', views.add_tool, name='add_tool'),
    path('tools/edit/<int:pk>/', views.edit_tool, name='edit_tool'),
    path('tools/delete/<int:pk>/', views.delete_tool, name='delete_tool'),
    path('my-tools/', views.my_tools, name='my_tools'),
    path('tool/<int:id>/', views.tool_detail, name='tool_detail'),

    # ======================== JOBS ========================
    path('jobs/', views.job_list, name='jobs_list'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('post-job/', views.post_job, name='post_job'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('job/edit/<int:pk>/', views.edit_job, name='edit_job'),
    path('job/delete/<int:pk>/', views.delete_job, name='delete_job'),
    path('job/complete/<int:pk>/', views.complete_job, name='complete_job'),

    # ======================== WORKER ========================
    path('worker/jobs/', views.worker_job_list, name='worker_job_list'),
    path('worker/job/<int:pk>/', views.worker_job_detail, name='worker_job_detail'),
    path('worker/applications/', views.worker_my_applications, name='worker_applications'),
    path('worker/save-job/<int:job_id>/', views.save_job, name='save_job'),
    path('worker/unsave-job/<int:job_id>/', views.unsave_job, name='unsave_job'),
    # ======================== FARMER ========================
    path('farmer/applications/', views.farmer_job_applications, name='farmer_job_applications'),

    # ======================== PUBLIC SUBSIDY ========================
    path("subsidies/", views.subsidy_list, name="subsidy_list"),

    path('subsidy/apply/<int:subsidy_id>/', views.apply_subsidy, name='apply_subsidy'),

    # ======================== ADMIN PANEL (CLEAN & PERFECT) ========================
    path('admin-panel/', views.dashboard, name='admin_dashboard'),

    # ADMIN — SUBSIDY MANAGEMENT (THESE ARE THE ONLY CORRECT ONES)
    path('admin/subsidies/', views.admin_subsidy_list, name='admin_subsidy_list'),
    path('admin/subsidy/applications/', views.admin_subsidy_applications, name='admin_subsidy_applications'),
    path('admin/subsidy/add/', views.admin_add_subsidy, name='admin_add_subsidy'),
    path('admin/subsidy/edit/<int:pk>/', views.admin_edit_subsidy, name='admin_edit_subsidy'),
    path('admin/subsidy/delete/<int:pk>/', views.admin_delete_subsidy, name='admin_delete_subsidy'),
    path('admin/subsidy/review/<int:app_id>/', views.admin_review_application, name='admin_review_application'),

    # ADMIN — OTHER PAGES
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/jobs/', views.admin_jobs, name='admin_jobs'),
    path('admin-panel/jobs/delete/<int:pk>/', views.admin_delete_job, name='admin_delete_job'),
    path('admin-panel/crops/', views.admin_crops, name='admin_crops'),
    path('admin-panel/crops/delete/<int:pk>/', views.admin_delete_crop, name='admin_delete_crop'),
    path('admin-panel/tools/', views.admin_tools, name='admin_tools'),
    path('admin-panel/tools/delete/<int:pk>/', views.admin_delete_tool, name='admin_delete_tool'),
    path('admin-panel/login-as/<int:user_id>/', views.admin_login_as_user, name='admin_login_as_user'),
]

# ======================== PASSWORD RESET ========================
urlpatterns += [
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='mainapp/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='mainapp/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='mainapp/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='mainapp/password_reset_complete.html'), name='password_reset_complete'),
]