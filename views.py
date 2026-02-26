# mainapp/views.py — FINAL UPDATED VERSION

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .models import (
    Crop, Tool, Job, Subsidy, SubsidyApplication, UserProfile,
    WorkerJobApplication, SavedJob,
    SKILL_CHOICES, EXPERIENCE_CHOICES, AVAILABILITY_CHOICES,
    ToolCategory,SellerType
)
from .forms import (
    RegisterForm, ProfileForm, CropForm, ToolForm,
    JobForm, WorkerJobApplicationForm
)

# ========================
# GUEST & AUTH VIEWS
# ========================

def welcome(request):
    return render(request, 'mainapp/welcome.html')


# ========================
# HOME PAGE
# ========================

def home(request):
    # Latest Crops (not sold)
    latest_crops = Crop.objects.filter(is_sold=False).order_by('-created_at')[:6]

    # Latest Tools (not sold)
    popular_tools = Tool.objects.filter(is_sold=False).order_by('-created_at')[:6]

    # Simple categories (even if template no longer uses all of these)
    crop_categories = [
        'vegetables', 'fruits', 'cereals', 'pulses', 'oilseeds', 'spices'
    ]

    # Tool categories – safe fallback if ToolCategory is empty
    try:
        tool_categories = [(c.id, c.name) for c in ToolCategory.objects.all()]
    except Exception:
        tool_categories = [
            ('tractor', 'Tractor & Machinery'),
            ('sprayer', 'Sprayers'),
            ('irrigation', 'Irrigation Tools'),
            ('soil', 'Soil Preparation'),
            ('harvesting', 'Harvesting Tools'),
            ('manual', 'Manual Tools'),
        ]

    context = {
        'latest_crops': latest_crops,
        'popular_tools': popular_tools,
        'crop_categories': crop_categories,
        'tool_categories': tool_categories,
    }
    return render(request, 'mainapp/home.html', context)


# ========================
# GLOBAL SEARCH
# ========================

def search(request):
    query = request.GET.get('q', '').strip()

    if query:
        crops = Crop.objects.filter(is_sold=False, name__icontains=query)
        tools = Tool.objects.filter(is_sold=False, name__icontains=query)
        jobs = (
            Job.objects.filter(is_completed=False, title__icontains=query) |
            Job.objects.filter(is_completed=False, description__icontains=query)
        )
    else:
        crops = Crop.objects.none()
        tools = Tool.objects.none()
        jobs = Job.objects.none()

    context = {
        'query': query,
        'crops': crops,
        'tools': tools,
        'jobs': jobs,
        'has_results': crops.exists() or tools.exists() or jobs.exists(),
    }
    return render(request, 'mainapp/search_results.html', context)


# ========================
# REGISTER / LOGIN / LOGOUT
# ========================

# ──────────────────────────────────────────────────────────────
# REPLACE YOUR ENTIRE register() FUNCTION WITH THIS ONE
# ──────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────
# FINAL FIXED register() — WORKS 100% (No IntegrityError + Correct Role)
# ──────────────────────────────────────────────────────────────
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            # THIS IS THE ONLY PLACE WE CREATE THE PROFILE
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone': form.cleaned_data['phone'],
                    'role': form.cleaned_data['role'],
                }
            )

            login(request, user)
            messages.success(request, f"Welcome! You are now a {form.cleaned_data['role'].title()}.")
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, "mainapp/register.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = 'mainapp/login.html'

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        messages.success(self.request, f"Welcome back, {user.username}!")
        return redirect('dashboard')

def custom_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('welcome')


# ========================
# DASHBOARD & PROFILE
# ========================

@login_required
def dashboard(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=request.user,
            phone="0000000000",
            role="buyer"
        )
    user = request.user
    role = profile.role
    context = {"profile": profile, "role": role}

    # ====================== ADMIN DASHBOARD =======================
    if request.user.is_staff:
        context.update({
            "role": "admin",
            "admin_stats": {
                "total_farmers": UserProfile.objects.filter(role__in=["farmer", "crop_seller"]).count(),
                "total_workers": UserProfile.objects.filter(role="worker").count(),
                "total_tool_sellers": UserProfile.objects.filter(role="tool_seller").count(),
                "total_buyers": UserProfile.objects.filter(role="buyer").count(),
                "active_jobs": Job.objects.filter(is_completed=False).count(),
                "pending_subsidies": SubsidyApplication.objects.filter(status="pending").count(),
            }
        })
        return render(request, "mainapp/dashboard.html", context)

    # ====================== FARMERS & CROP SELLERS =======================
    if role in ["farmer", "crop_seller"]:
        context["my_crops"] = Crop.objects.filter(seller=request.user)[:6]
        context["total_crops"] = Crop.objects.filter(seller=request.user).count()
        context["active_crops"] = Crop.objects.filter(seller=request.user, is_sold=False).count()

    if role == "farmer":
        context["my_jobs"] = Job.objects.filter(posted_by=request.user)[:6]
        context["my_subsidies"] = SubsidyApplication.objects.filter(farmer=request.user).select_related("subsidy")[:10]
        context["total_subsidies"] = Subsidy.objects.filter(is_active=True).count()
        context["applied_subsidies"] = SubsidyApplication.objects.filter(farmer=request.user).count()
        context["pending_subsidies"] = SubsidyApplication.objects.filter(farmer=request.user, status="pending").count()
        context["approved_subsidies"] = SubsidyApplication.objects.filter(farmer=request.user, status="approved").count()

    # ====================== TOOL SELLER =======================
    if role == "tool_seller":
        context["my_tools"] = Tool.objects.filter(seller=request.user)[:6]

    # ====================== WORKER =======================
    if role == "worker":
        total_apps = WorkerJobApplication.objects.filter(worker=user).count()

        context.update({
            "total_applications": total_apps,
        })
        return render(request, "mainapp/dashboard.html", context)

    # ====================== BUYER DEFAULT =======================
    if role == "buyer":
        context["recent_tools"] = Tool.objects.filter(is_sold=False).order_by("-created_at")[:6]
        context["recent_crops"] = Crop.objects.filter(is_sold=False).order_by("-created_at")[:6]

    return render(request, "mainapp/dashboard.html", context)


@login_required
def profile(request):
    profile = request.user.userprofile

    # Worker extras
    if profile.role == 'worker':
        worker_data = {
            'skills': profile.worker_skills or [],
            'experience': profile.worker_experience,
            'expected_wage': profile.worker_expected_wage,
            'availability': profile.worker_availability,
            'bio': profile.worker_bio,
        }
    else:
        worker_data = None

    # Buyer extras
    if profile.role == 'buyer':
        recent_crops = Crop.objects.filter(is_sold=False).order_by('-created_at')[:5]
        recent_tools = Tool.objects.filter(is_sold=False).order_by('-created_at')[:5]
    else:
        recent_crops = []
        recent_tools = []

    return render(request, 'mainapp/profile.html', {
        'profile': profile,
        'worker_data': worker_data,
        'recent_crops': recent_crops,
        'recent_tools': recent_tools,
    })


@login_required
def profile_edit(request):
    profile = request.user.userprofile
    is_worker = profile.role == "worker"

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()   # Saves common fields from ProfileForm

            # =============== WORKER-SPECIFIC FIELDS ===============
            if is_worker:

                # SKILLS (multi-select)
                skills = request.POST.getlist("worker_skills")
                profile.worker_skills = skills if skills else []

                # EXPERIENCE
                profile.worker_experience = request.POST.get("worker_experience") or ""

                # EXPECTED WAGE (safe conversion)
                wage = request.POST.get("worker_expected_wage")
                profile.worker_expected_wage = (
                    int(wage) if wage and wage.isdigit() else None
                )

                # AVAILABILITY
                profile.worker_availability = (
                    request.POST.get("worker_availability") or ""
                )

                # BIO
                profile.worker_bio = request.POST.get("worker_bio") or ""

                # LOCATION FIELDS
                profile.worker_village = request.POST.get("worker_village") or ""
                profile.worker_mandal = request.POST.get("worker_mandal") or ""
                profile.worker_district = request.POST.get("worker_district") or ""

                profile.save()

            messages.success(request, "Profile updated successfully!")
            return redirect("profile")

    else:
        form = ProfileForm(instance=profile)

    # =============== CONTEXT ===============
    return render(
        request,
        "mainapp/profile_edit.html",
        {
            "form": form,
            "profile": profile,
            "role": profile.role,
            "is_worker": is_worker,
            "SKILL_CHOICES": SKILL_CHOICES,
            "EXPERIENCE_CHOICES": EXPERIENCE_CHOICES,
            "AVAILABILITY_CHOICES": AVAILABILITY_CHOICES,
        },
    )


# ========================
# CROP VIEWS
# ========================

def crop_list(request):
    crops = Crop.objects.filter(is_sold=False).select_related('seller__userprofile')
    return render(request, 'mainapp/crop_list.html', {'crops': crops})


@login_required
def my_crops(request):
    if request.user.userprofile.role not in ['farmer', 'crop_seller']:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    crops = Crop.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'mainapp/my_crops.html', {'crops': crops})


@login_required
def add_crop(request):
    if request.user.userprofile.role not in ['farmer', 'crop_seller']:
        messages.error(request, "Only farmers and crop sellers can add crops.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.seller = request.user
            crop.save()
            messages.success(request, "Crop added successfully!")
            return redirect('my_crops')
    else:
        form = CropForm()
    return render(request, 'mainapp/add_crop.html', {'form': form})


@login_required
def edit_crop(request, pk):
    crop = get_object_or_404(Crop, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES, instance=crop)
        if form.is_valid():
            form.save()
            messages.success(request, "Crop updated!")
            return redirect('my_crops')
    else:
        form = CropForm(instance=crop)
    return render(request, 'mainapp/edit_crop.html', {'form': form, 'crop': crop})


@login_required
def delete_crop(request, pk):
    crop = get_object_or_404(Crop, pk=pk, seller=request.user)
    if request.method == 'POST':
        crop.delete()
        messages.success(request, "Crop deleted.")
        return redirect('my_crops')
    return render(request, 'mainapp/delete_crop.html', {'crop': crop})


# ========================
# TOOL VIEWS
# ========================


def tool_list(request):
    tools = Tool.objects.filter(is_sold=False).select_related('seller__userprofile', 'category', 'seller_type')

    categories = ToolCategory.objects.all()
    seller_types = SellerType.objects.all()

    # Filters
    if request.GET.get('category'):
        tools = tools.filter(category_id=request.GET['category'])
    if request.GET.get('seller_type'):
        tools = tools.filter(seller_type_id=request.GET['seller_type'])
    if request.GET.get('q'):
        q = request.GET['q']
        tools = tools.filter(Q(name__icontains=q) | Q(description__icontains=q))

    return render(request, 'mainapp/tool_list.html', {
        'tools': tools,
        'categories': categories,
        'seller_types': seller_types,   # ✔ CORRECT FIX
        'selected_category': request.GET.get('category'),
        'selected_seller_type': request.GET.get('seller_type'),
    })

def tool_detail(request, id):
    tool = get_object_or_404(Tool, id=id)
    return render(request, 'mainapp/tool_detail.html', {'tool': tool})


@login_required
def my_tools(request):
    if request.user.userprofile.role != 'tool_seller':
        messages.error(request, "Only tool sellers can view this page.")
        return redirect('dashboard')
    tools = Tool.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'mainapp/my_tools.html', {'my_tools': tools})


# ========== ADD TOOL — NOW SHOWS CATEGORIES & SELLER TYPE ==========
@login_required
def add_tool(request):
    if request.user.userprofile.role != 'tool_seller':
        messages.error(request, "Only tool sellers can add tools.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ToolForm(request.POST, request.FILES)
        if form.is_valid():
            tool = form.save(commit=False)
            tool.seller = request.user
            tool.save()
            messages.success(request, f"{tool.name} added successfully!")
            return redirect('my_tools')
    else:
        form = ToolForm()

    # THIS LINE WAS MISSING — NOW CATEGORIES SHOW IN FORM!
    return render(request, 'mainapp/add_tool.html', {
        'form': form,
        'title': 'Add New Tool / Machinery',
        'categories': ToolCategory.objects.all().order_by('name'),
    })

# ========== EDIT TOOL — NOW SHOWS CURRENT CATEGORY & SELLER TYPE ==========
@login_required
def edit_tool(request, pk):
    tool = get_object_or_404(Tool, pk=pk, seller=request.user)
    
    if request.method == 'POST':
        form = ToolForm(request.POST, request.FILES, instance=tool)
        if form.is_valid():
            form.save()
            messages.success(request, "Tool updated successfully!")
            return redirect('my_tools')
    else:
        form = ToolForm(instance=tool)

    # THIS LINE WAS MISSING — NOW FORM SHOWS CURRENT VALUES!
    return render(request, 'mainapp/edit_tool.html', {
        'form': form,
        'tool': tool,
        'title': 'Add New Tool / Machinery',
        'categories': ToolCategory.objects.all().order_by('name'),
    })

@login_required
def delete_tool(request, pk):
    tool = get_object_or_404(Tool, pk=pk, seller=request.user)
    if request.method == 'POST':
        tool.delete()
        messages.success(request, "Tool deleted.")
        return redirect('my_tools')
    return render(request, 'mainapp/delete_tool.html', {'tool': tool})


# ========================
# JOB VIEWS
# ========================

def job_list(request):
    jobs = Job.objects.filter(is_completed=False).order_by('-created_at')
    return render(request, 'mainapp/job_list.html', {'jobs': jobs})


@login_required
def post_job(request):
    if request.user.userprofile.role != 'farmer':
        messages.error(request, "Only farmers can post jobs.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            messages.success(request, "Job posted!")
            return redirect('my_jobs')
    else:
        form = JobForm()
    return render(request, 'mainapp/post_job.html', {'form': form})


@login_required
def my_jobs(request):
    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')
    jobs = Job.objects.filter(posted_by=request.user).order_by('-created_at')
    return render(request, 'mainapp/my_jobs.html', {'jobs': jobs})


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(request, 'mainapp/job_detail.html', {'job': job})


@login_required
def edit_job(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated!")
            return redirect('my_jobs')
    else:
        form = JobForm(instance=job)
    return render(request, 'mainapp/edit_job.html', {'form': form, 'job': job})


@login_required
def delete_job(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    if request.method == 'POST':
        job.delete()
        messages.success(request, "Job deleted.")
        return redirect('my_jobs')
    return render(request, 'mainapp/delete_job.html', {'job': job})


@login_required
def complete_job(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    if request.method == 'POST':
        job.is_completed = True
        job.save()
        messages.success(request, "Job marked as completed!")
    return redirect('my_jobs')


# ========================
# WORKER VIEWS
# ========================

@login_required
def worker_job_list(request):
    if request.user.userprofile.role != 'worker':
        messages.error(request, "Workers only.")
        return redirect('dashboard')

    jobs = Job.objects.filter(is_completed=False).order_by('-created_at')
    saved_ids = SavedJob.objects.filter(worker=request.user).values_list('job_id', flat=True)
    return render(request, 'mainapp/worker_job_list.html', {'jobs': jobs, 'saved_ids': saved_ids})


@login_required
def worker_job_detail(request, pk):
    if request.user.userprofile.role != 'worker':
        return redirect('dashboard')

    job = get_object_or_404(Job, pk=pk, is_completed=False)
    already_applied = WorkerJobApplication.objects.filter(worker=request.user, job=job).exists()
    is_saved = SavedJob.objects.filter(worker=request.user, job=job).exists()

    if request.method == 'POST':
        if 'save' in request.POST:
            SavedJob.objects.get_or_create(worker=request.user, job=job)
            messages.success(request, "Job saved!")
        elif 'unsave' in request.POST:
            SavedJob.objects.filter(worker=request.user, job=job).delete()
            messages.success(request, "Job removed from saved")
        elif 'apply' in request.POST and not already_applied:
            WorkerJobApplication.objects.create(
                worker=request.user,
                job=job,
                expected_wage=request.user.userprofile.worker_expected_wage or 600,
                availability=request.user.userprofile.worker_availability or 'immediate'
            )
            messages.success(request, "Applied successfully!")
            already_applied = True

    return render(request, 'mainapp/worker_job_detail.html', {
        'job': job,
        'already_applied': already_applied,
        'is_saved': is_saved,
    })


@login_required
def worker_my_applications(request):
    if request.user.userprofile.role != 'worker':
        return redirect('dashboard')

    applications = WorkerJobApplication.objects.filter(
        worker=request.user
    ).select_related('job', 'job__posted_by__userprofile')
    return render(request, 'mainapp/worker_my_applications.html', {'applications': applications})


@login_required
def save_job(request, job_id):
    if request.user.userprofile.role != 'worker':
        return redirect('dashboard')

    job = get_object_or_404(Job, id=job_id)
    SavedJob.objects.get_or_create(worker=request.user, job=job)
    messages.success(request, "Job saved!")
    return redirect('worker_job_list')


@login_required
def unsave_job(request, job_id):
    SavedJob.objects.filter(worker=request.user, job__id=job_id).delete()
    messages.info(request, "Job removed from saved.")
    return redirect('worker_job_list')


# ========================
# FARMER VIEWING APPLICATIONS
# ========================

@login_required
def farmer_job_applications(request):
    if request.user.userprofile.role != 'farmer':
        messages.error(request, "Only farmers can view applications.")
        return redirect('dashboard')

    applications = WorkerJobApplication.objects.filter(
        job__posted_by=request.user
    ).select_related('worker__userprofile', 'job')

    if request.method == 'POST':
        app_id = request.POST.get('app_id')
        action = request.POST.get('action')
        app = get_object_or_404(WorkerJobApplication, id=app_id, job__posted_by=request.user)

        if action == 'approve':
            app.status = 'approved'
        elif action == 'reject':
            app.status = 'rejected'
        app.save()
        messages.success(request, f"Application {app.get_status_display().lower()}!")

    return render(request, 'mainapp/farmer_applications.html', {'applications': applications})


# ========================
# SUBSIDY VIEWS
# ========================

@login_required
def subsidy_list(request):
    # Everyone can VIEW subsidies. Only farmers can apply.
    subsidies = Subsidy.objects.filter(is_active=True)

    if request.user.is_authenticated:
        applied_ids = SubsidyApplication.objects.filter(
            farmer=request.user
        ).values_list('subsidy_id', flat=True)
        role = request.user.userprofile.role
    else:
        applied_ids = []
        role = None

    return render(request, 'mainapp/subsidy_list.html', {
        'subsidies': subsidies,
        'applied_ids': applied_ids,
        'role': role,
    })



@login_required
def apply_subsidy(request, subsidy_id):
    subsidy = get_object_or_404(Subsidy, id=subsidy_id, is_active=True)

    if request.user.userprofile.role != 'farmer':
        return redirect('dashboard')

    if SubsidyApplication.objects.filter(farmer=request.user, subsidy=subsidy).exists():
        messages.info(request, "You have already applied.")
        return redirect('subsidy_list')

    if request.method == 'POST':
        SubsidyApplication.objects.create(farmer=request.user, subsidy=subsidy)
        messages.success(request, "Application submitted!")
        return redirect('dashboard')

    return render(request, 'mainapp/apply_subsidy.html', {'subsidy': subsidy})


# ========================
# ADMIN VIEWS
# ========================

@staff_member_required
def admin_dashboard(request):
    context = {
        'total_farmers': UserProfile.objects.filter(role='farmer').count(),
        'total_workers': UserProfile.objects.filter(role='worker').count(),
        'total_jobs': Job.objects.filter(is_completed=False).count(),
        'total_crops': Crop.objects.filter(is_sold=False).count(),
        'total_tools': Tool.objects.filter(is_sold=False).count(),
        'pending_subsidies': SubsidyApplication.objects.filter(status='pending').count(),
    }
    return render(request, 'mainapp/admin_dashboard.html', context)


@staff_member_required
def admin_users(request):
    users = UserProfile.objects.select_related('user').all().order_by('-user__date_joined')
    return render(request, 'mainapp/admin_users.html', {'users': users})


@staff_member_required
def admin_jobs(request):
    jobs = Job.objects.select_related('posted_by__userprofile').all()
    return render(request, 'mainapp/admin_jobs.html', {'jobs': jobs})


@staff_member_required
def admin_crops(request):
    crops = Crop.objects.select_related('seller__userprofile').filter(is_sold=False)
    return render(request, 'mainapp/admin_crops.html', {'crops': crops})


@staff_member_required
def admin_tools(request):
    tools = Tool.objects.select_related('seller__userprofile').filter(is_sold=False)
    return render(request, 'mainapp/admin_tools.html', {'tools': tools})


@staff_member_required
def admin_login_as_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    login(request, user)
    messages.success(request, f"Now logged in as {user.get_full_name() or user.username}")
    return redirect('dashboard')


# ===== SUBSIDY ADMIN =====

@staff_member_required
def admin_subsidy_list(request):
    subsidies = Subsidy.objects.all().order_by('-is_active', '-created_at')
    return render(request, 'mainapp/admin_subsidy_list.html', {'subsidies': subsidies})


@staff_member_required
def admin_add_subsidy(request):
    if request.method == 'POST':
        Subsidy.objects.create(
            name=request.POST['name'],
            short_description=request.POST['short_description'],
            full_description=request.POST['full_description'],
            benefit_amount=request.POST['benefit_amount'],
            eligibility_criteria=request.POST['eligibility_criteria'],
            required_documents=request.POST['required_documents'],
            application_deadline=request.POST.get('application_deadline') or None,
            is_active='is_active' in request.POST
        )
        messages.success(request, "New subsidy scheme created!")
        return redirect('admin_subsidy_list')
    return render(request, 'mainapp/admin_add_subsidy.html')


@staff_member_required
def admin_edit_subsidy(request, pk):
    subsidy = get_object_or_404(Subsidy, pk=pk)
    if request.method == 'POST':
        subsidy.name = request.POST['name']
        subsidy.short_description = request.POST['short_description']
        subsidy.full_description = request.POST['full_description']
        subsidy.benefit_amount = request.POST['benefit_amount']
        subsidy.eligibility_criteria = request.POST['eligibility_criteria']
        subsidy.required_documents = request.POST['required_documents']
        subsidy.application_deadline = request.POST.get('application_deadline') or None
        subsidy.is_active = 'is_active' in request.POST
        subsidy.save()
        messages.success(request, "Subsidy updated!")
        return redirect('admin_subsidy_list')
    return render(request, 'mainapp/admin_edit_subsidy.html', {'subsidy': subsidy})


@staff_member_required
def admin_delete_subsidy(request, pk):
    subsidy = get_object_or_404(Subsidy, pk=pk)
    if request.method == 'POST':
        subsidy.delete()
        messages.success(request, "Subsidy scheme deleted.")
        return redirect('admin_subsidy_list')
    return render(request, 'mainapp/admin_confirm_delete.html', {
        'object': subsidy,
        'object_type': 'Subsidy Scheme',
        'back_url': 'admin_subsidy_list',
    })


@staff_member_required
def admin_subsidy_applications(request):
    applications = SubsidyApplication.objects.select_related(
        'farmer__userprofile', 'subsidy'
    ).all().order_by('-applied_at')
    return render(request, 'mainapp/admin_subsidy_applications.html', {'applications': applications})


@staff_member_required
def admin_review_application(request, app_id):
    app = get_object_or_404(SubsidyApplication, id=app_id)

    if request.method == 'POST':
        # Match template: buttons have name="action" value="approved"/"rejected"
        action = request.POST.get('action')
        notes = request.POST.get('admin_notes', '')

        if action not in ['approved', 'rejected']:
            messages.error(request, "Please choose Approve or Reject.")
            return redirect('admin_review_application', app_id=app_id)

        app.status = action
        app.admin_notes = notes
        app.reviewed_at = timezone.now()
        app.save()

        messages.success(request, f"Application {app.get_status_display().lower()}!")
        return redirect('admin_subsidy_applications')

    return render(request, 'mainapp/admin_review_application.html', {'app': app})


# ===== GENERIC ADMIN DELETE HELPERS =====

@staff_member_required
def admin_delete_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        job.delete()
        messages.success(request, "Job deleted by admin.")
        return redirect('admin_jobs')
    return render(request, 'mainapp/admin_confirm_delete.html', {
        'object': job,
        'object_type': 'Job',
        'back_url': 'admin_jobs',
    })


@staff_member_required
def admin_delete_crop(request, pk):
    crop = get_object_or_404(Crop, pk=pk)
    if request.method == 'POST':
        crop.delete()
        messages.success(request, "Crop listing deleted by admin.")
        return redirect('admin_crops')
    return render(request, 'mainapp/admin_confirm_delete.html', {
        'object': crop,
        'object_type': 'Crop',
        'back_url': 'admin_crops',
    })


@staff_member_required
def admin_delete_tool(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    if request.method == 'POST':
        tool.delete()
        messages.success(request, "Tool listing deleted by admin.")
        return redirect('admin_tools')
    return render(request, 'mainapp/admin_confirm_delete.html', {
        'object': tool,
        'object_type': 'Tool',
        'back_url': 'admin_tools',
    })
