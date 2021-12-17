from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery
import admin_thumbnails


# Register your models here.


@admin_thumbnails.thumbnail('image', background=True)
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_name', 'price', 'stock', 'category', 'modified_date', 'is_available')
    prepopulated_fields = {'slug':('product_name',)}
    inlines = [ProductGalleryInline]


@admin.register(Variation)
class VariationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')

admin.site.register(ReviewRating)
admin.site.register(ProductGallery)