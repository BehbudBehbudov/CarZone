from django.contrib import admin
from .models import Category, Car, CarImage, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'price', 'year', 'is_sold')
    list_filter = ('category', 'fuel_type', 'transmission', 'condition')
    search_fields = ('title', 'description')

admin.site.register(CarImage)

admin.site.register(Comment)