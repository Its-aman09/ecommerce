from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Review

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'available', 'created_at']
    list_filter = ['available', 'category', 'created_at']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_per_page = 20

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    raw_id_fields = ['product']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'created_at', 'get_total_items']
    list_filter = ['created_at']
    inlines = [CartItemInline]
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ['product']
    readonly_fields = ['price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'email', 'total_amount', 'status', 'paid', 'created_at']
    list_filter = ['status', 'paid', 'created_at']
    list_editable = ['status', 'paid']
    search_fields = ['user__username', 'email', 'first_name', 'last_name']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'paid', 'total_amount')
        }),
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'state', 'zip_code')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']
    readonly_fields = ['created_at']