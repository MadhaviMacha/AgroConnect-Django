from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

User = get_user_model()
# ========================
# GLOBAL CHOICES
# ========================

SKILL_CHOICES = [
    ('ploughing', 'Ploughing'),
    ('sowing', 'Sowing'),
    ('weeding', 'Weeding'),
    ('harvesting', 'Harvesting'),
    ('spraying', 'Spraying'),
    ('tractor_driving', 'Tractor Driving'),
    ('irrigation', 'Irrigation'),
    ('livestock', 'Livestock Care'),
    ('packing', 'Packing'),
    ('loading', 'Loading/Unloading'),
]

EXPERIENCE_CHOICES = [
    ('0-1', '0–1 year'),
    ('1-3', '1–3 years'),
    ('3-5', '3–5 years'),
    ('5+', '5+ years'),
]

AVAILABILITY_CHOICES = [
    ('immediate', 'Immediately'),
    ('7_days', 'Within 7 days'),
    ('15_days', 'Within 15 days'),
    ('30_days', 'Within 30 days'),
    ('not_available', 'Not Available Right Now'),
]

# ========================
# CROP CATEGORIES — 10 PROFESSIONAL
# ========================

CROP_CATEGORY_CHOICES = [
    ('food_grains', 'Food Grains (Rice, Wheat, Maize, Jowar, Bajra, Ragi)'),
    ('pulses', 'Pulses (Toor, Moong, Urad, Chana, Masoor)'),
    ('oilseeds', 'Oilseeds (Groundnut, Sunflower, Mustard, Soybean)'),
    ('fruits', 'Fruits (Mango, Banana, Papaya, Pomegranate, Guava)'),
    ('vegetables', 'Vegetables (Tomato, Onion, Potato, Brinjal, Chilli)'),
    ('leafy_veg', 'Leafy Vegetables (Spinach, Methi, Coriander, Amaranth)'),
    ('cash_crops', 'Cash Crops (Cotton, Sugarcane, Tobacco)'),
    ('spices', 'Spices (Turmeric, Ginger, Garlic, Red Chilli, Cumin)'),
    ('plantation', 'Plantation Crops (Coconut, Arecanut, Oil Palm)'),
    ('flowers', 'Flowers & Ornamental (Rose, Marigold, Jasmine, Lotus)'),
]

# ========================
# USER PROFILE
# ========================

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('crop_seller', 'Crop Seller'),
        ('tool_seller', 'Tool Seller'),
        ('worker', 'Worker'),
        ('admin', 'Admin'),
        ('buyer', 'Buyer'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.TextField(blank=True)

    # Worker-specific fields
    worker_skills = models.JSONField(default=list, blank=True)
    worker_experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES, blank=True, default='')
    worker_expected_wage = models.PositiveIntegerField(null=True, blank=True)
    worker_availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, blank=True, default='')
    worker_village = models.CharField(max_length=100, blank=True)
    worker_mandal = models.CharField(max_length=100, blank=True)
    worker_district = models.CharField(max_length=100, blank=True)
    worker_bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"

# ========================
# CROP MODEL — FINAL ELITE VERSION
# ========================

class Crop(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crops')
    name = models.CharField(max_length=100, help_text="e.g. BPT Rice, Red Onion, Alphonso Mango")
    category = models.CharField(max_length=20, choices=CROP_CATEGORY_CHOICES, default='food_grains')
    
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per kg in ₹")
    quantity = models.PositiveIntegerField(help_text="Available quantity in kg")
    image = models.ImageField(upload_to='crops/', blank=True, null=True)
    location = models.CharField(max_length=150, help_text="Village, Mandal, District")
    description = models.TextField(blank=True, help_text="Quality, variety, organic, etc.")
    
    is_sold = models.BooleanField(default=False, help_text="Mark as sold when no longer available")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Crop Listing"
        verbose_name_plural = "Crop Listings"

    def __str__(self):
        sold = " [SOLD]" if self.is_sold else ""
        return f"{self.name} - ₹{self.price}/kg ({self.quantity}kg){sold}"

    def get_category_display_name(self):
        return dict(CROP_CATEGORY_CHOICES).get(self.category, self.category)

# ========================
# TOOL RELATED MODELS
# ========================

class SellerType(models.Model):
    TYPE_CHOICES = [
        ('small_vendor', 'Small Vendor'),
        ('used_seller', 'Second-Hand / Used Tool Seller'),
        ('rental_provider', 'Lessor / Rental Provider'),
        ('commercial', 'Company / Commercial Seller'),
    ]
    name = models.CharField(max_length=20, choices=TYPE_CHOICES, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.get_name_display()

class ToolCondition(models.Model):
    CONDITION_CHOICES = [
        ('used_good', 'Used – Good'),
        ('used_very_good', 'Used – Very Good'),
        ('refurbished', 'Refurbished'),
    ]
    name = models.CharField(max_length=20, choices=CONDITION_CHOICES)

    def __str__(self):
        return self.get_name_display()

class ToolCategory(models.Model):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories')
    icon = models.CharField(max_length=30, default='bi bi-tools')

    class Meta:
        verbose_name_plural = "Tool Categories"

    def __str__(self):
        return self.name

    def get_full_path(self):
        if self.parent:
            return f"{self.parent.get_full_path()} → {self.name}"
        return self.name

class Tool(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tools')
    seller_type = models.ForeignKey(SellerType, on_delete=models.SET_NULL, null=True)

    name = models.CharField(max_length=100)
    category = models.ForeignKey(ToolCategory, on_delete=models.SET_NULL, null=True, related_name='tools')
    condition = models.ForeignKey(ToolCondition, on_delete=models.SET_NULL, null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    rental_price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    rental_price_per_day = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    quantity = models.PositiveIntegerField(default=1)
    is_rental = models.BooleanField(default=False)
    is_sold = models.BooleanField(default=False)
    sold_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_tools')
    sold_at = models.DateTimeField(null=True, blank=True)

    front_image = models.ImageField(upload_to='tools/front/', null=True, blank=True)
    side_image = models.ImageField(upload_to='tools/side/', null=True, blank=True)
    usage_image = models.ImageField(upload_to='tools/usage/', null=True, blank=True)

    description = models.TextField()
    terms_conditions = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        rental = " (Rental)" if self.is_rental else ""
        return f"{self.name} - ₹{self.price}{rental}"

    def is_available(self):
        return self.quantity > 0 and not self.is_sold



# ========================
# JOB & WORKER MODELS
# ========================

class Job(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    wage = models.IntegerField()
    location = models.CharField(max_length=100)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    duration = models.CharField(max_length=50, blank=True)
    workers_needed = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.title} - {self.location}"

class WorkerJobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='worker_applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='worker_applications')
    expected_wage = models.PositiveIntegerField()
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('worker', 'job')

class SavedJob(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('worker', 'job')

# ========================
# SUBSIDY MODELS
# ========================

# models.py
class Subsidy(models.Model):
    name = models.CharField(max_length=200)
    short_description = models.CharField(max_length=300)
    full_description = models.TextField()
    benefit_amount = models.CharField(max_length=150, blank=True, null=True)
    eligibility_criteria = models.TextField()
    required_documents = models.TextField()
    application_deadline = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Subsidies"


class SubsidyApplication(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'))
    
    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    subsidy = models.ForeignKey(Subsidy, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('farmer', 'subsidy')  # One application per scheme per farmer