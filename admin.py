from django.contrib import admin
from .models import *

@admin.register(SellerType)
class SellerTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(ToolCondition)
class ToolConditionAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'seller_type', 'price', 'is_rental', 'is_sold')
    list_filter = ('seller_type', 'is_rental', 'category')
    search_fields = ('name', 'seller__username')