from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    UserProfile, Crop, Tool, Job, WorkerJobApplication,
    SellerType, ToolCategory, ToolCondition, Subsidy, CROP_CATEGORY_CHOICES
)
from .models import SKILL_CHOICES, EXPERIENCE_CHOICES, AVAILABILITY_CHOICES

# ========================
# USER REGISTRATION
# ========================

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    UserProfile, Crop, Tool, Job, WorkerJobApplication,
    SellerType, ToolCategory, ToolCondition, Subsidy, CROP_CATEGORY_CHOICES
)
from .models import SKILL_CHOICES, EXPERIENCE_CHOICES, AVAILABILITY_CHOICES


# ========================
# USER REGISTRATION
# ========================

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last Name'
        })
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Username'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email address'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '10-digit Phone'
        })
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,   # includes 'buyer' now
        required=True,
        widget=forms.Select()
    )

    # Override password fields to add security attributes
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password',
            'oncopy': 'return false',
            'onpaste': 'return false',
            'oncut': 'return false',
        }),
        help_text=(
            "At least 8 characters, avoid common passwords and do not use only numbers."
        ),
    )

    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Re-enter password',
            'autocomplete': 'new-password',
            'oncopy': 'return false',
            'onpaste': 'return false',
            'oncut': 'return false',
        }),
        help_text="Enter the same password again for verification.",
    )

    class Meta:
        model = User
        # ✅ email added to fields
        fields = [
            'first_name', 'last_name', 'username',
            'email', 'phone', 'role',
            'password1', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields use Bootstrap big input styling,
        # but do NOT remove the password attributes.
        for name, field in self.fields.items():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing_class + ' form-control form-control-lg').strip()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and (not phone.isdigit() or len(phone) != 10):
            raise forms.ValidationError("Phone must be exactly 10 digits.")
        if UserProfile.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This phone is already registered.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email



# ========================
# PROFILE EDIT
# ========================

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'photo', 'address']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit phone'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


# ========================
# CROP FORM — FINAL ELITE VERSION (WITH AUTOCOMPLETE + 10 CATEGORIES)
# ========================

# Full list of popular crop names for autocomplete
POPULAR_CROPS = [
    "Rice", "Basmati Rice", "Sona Masoori", "Wheat", "Maize", "Jowar", "Bajra", "Ragi",
    "Toor Dal", "Moong Dal", "Urad Dal", "Chana Dal", "Masoor Dal", "Groundnut", "Sunflower",
    "Mustard", "Soybean", "Mango", "Alphonso Mango", "Banana", "Papaya", "Pomegranate",
    "Guava", "Tomato", "Onion", "Red Onion", "Potato", "Brinjal", "Lady Finger", "Green Chilli",
    "Spinach", "Methi", "Coriander", "Cotton", "Sugarcane", "Turmeric", "Ginger", "Garlic",
    "Red Chilli", "Coconut", "Arecanut", "Rose", "Marigold", "Jasmine", "Lotus"
]

class CropForm(forms.ModelForm):
    # Smart Autocomplete Crop Name
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Start typing crop name... (e.g. Basmati Rice)',
            'list': 'crop-suggestions',
            'autocomplete': 'off'
        }),
        label="Crop Name",
        help_text="Type and choose from popular crops"
    )

    # Beautiful Category Dropdown
    category = forms.ChoiceField(
        choices=CROP_CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Category"
    )

    price = forms.DecimalField(
        min_value=1, max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price per kg (₹)'}),
        label="Price per kg"
    )

    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Available quantity in kg'}),
        label="Quantity (kg)"
    )

    location = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Village, Mandal, District'}),
        label="Location"
    )

    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        label="Crop Photo (Optional)"
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Quality, variety, organic, freshness...'}),
        label="Description (Optional)"
    )

    is_sold = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Mark as Sold (no longer available)"
    )

    class Meta:
        model = Crop
        fields = ['name', 'category', 'price', 'quantity', 'location', 'image', 'description', 'is_sold']


# ========================
# TOOL FORM (unchanged — already perfect)
# ========================

class ToolForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # THIS MAKES SELLER TYPE & CONDITION DROPDOWNS WORK
        self.fields['seller_type'].queryset = SellerType.objects.all()
        self.fields['category'].queryset = ToolCategory.objects.filter(parent=None).order_by('name')  # Only main categories
        self.fields['condition'].queryset = ToolCondition.objects.all()
        
        # Make optional fields
        for field in ['front_image', 'side_image', 'usage_image', 'condition']:
            self.fields[field].required = False

    class Meta:
        model = Tool
        fields = (
            'seller_type', 'name', 'category', 'condition',
            'price', 'is_rental',
            'rental_price_per_hour', 'rental_price_per_day', 'security_deposit',
            'quantity', 'front_image', 'side_image', 'usage_image',
            'description', 'terms_conditions'
        )
        widgets = {
            'seller_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': ' refreshing...form-select'}),
            'is_rental': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'terms_conditions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'seller_type': 'I am a',
            'is_rental': 'Available for Rent',
        }

# ========================
# JOB & WORKER FORMS
# ========================

# ========================

class JobForm(forms.ModelForm):
    title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'e.g. Paddy Harvesting, Tractor Ploughing, Weeding'
        }),
        label="Job Title"
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe the work, timing, tools needed, etc.'
        }),
        label="Job Description",
        help_text="Give clear details so workers understand the job"
    )

    wage = forms.IntegerField(
        min_value=200,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'e.g. 600'
        }),
        label="Daily Wage (₹)",
        help_text="Amount you will pay per day"
    )

    location = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Village, Mandal, District'
        }),
        label="Job Location"
    )

    duration = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 15 days, 1 month, 45-60 days'
        }),
        label="Job Duration",
        help_text="How long the work will last"
    )

    workers_needed = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'style': 'width: 120px;'
        }),
        label="Workers Needed"
    )

    class Meta:
        model = Job
        fields = ['title', 'description', 'wage', 'location', 'duration', 'workers_needed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make everything look premium
        for field_name, field in self.fields.items():
            if field_name != 'workers_needed':
                field.widget.attrs.setdefault('class', 'form-control')
class WorkerJobApplicationForm(forms.ModelForm):
    expected_wage = forms.IntegerField(
        min_value=200, max_value=5000,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Your expected daily wage'}),
        label="Expected Daily Wage (₹)"
    )
    availability = forms.ChoiceField(
        choices=AVAILABILITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="When can you start?"
    )

    class Meta:
        model = WorkerJobApplication
        fields = ['expected_wage', 'availability']


# ========================
# SUBSIDY FORM
# ========================

class SubsidyApplicationForm(forms.Form):
    pass  # Just a confirmation button