from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Product, Category, Cart, CartItem, Order, OrderItem
from django.utils.text import slugify
from .forms import ProductForm

def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    print(cart)
    return cart

def home(request):
    products = Product.objects.filter(available=True)[:8]
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories
    }
    return render(request, 'store/home.html', context)

def product_list(request):
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    context = {
        'products': products,
        'categories': categories
    }
    return render(request, 'store/product_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(
        category=product.category, 
        available=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'store/product_details.html', context)

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{product.name} added to cart!')
    return redirect('cart')

def cart_view(request):
    print('HERE!!!!!')
    cart = get_or_create_cart(request)
    print(cart)
    context = {
        'cart': cart
    }
    return render(request, 'store/cart.html', context)

def update_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated!')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart!')
    
    return redirect('cart')

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, 'Item removed from cart!')
    return redirect('cart')

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty!')
        return redirect('cart')
    
    if request.method == 'POST':
        # Create order
        order = Order.objects.create(
            user=request.user,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            zip_code=request.POST.get('zip_code'),
            total_amount=cart.get_total_price(),
            payment_method='cod'
        )
        
        # Create order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            
            # Update stock
            item.product.stock -= item.quantity
            item.product.save()
        
        # Clear cart
        cart.items.all().delete()
        
        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('order_success', order_id=order.id)
    
    context = {
        'cart': cart
    }
    return render(request, 'store/checkout.html', context)

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order
    }
    return render(request, 'store/order_success.html', context)

def create_product(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                product = form.save()
                messages.success(request, f'Product "{product.name}" created successfully!')
                return redirect('product_detail', slug=product.slug)
            
            except Exception as e:
                messages.error(request, f'Error creating product: {str(e)}')
        else:
            # If the form is not valid, the form itself will contain error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        # This part handles GET requests, creating a blank form
        form = ProductForm()

    return render(request, 'store/create_product.html', {'form': form, 'categories': categories})


def edit_product(request, slug):
    """View for editing existing products"""
    product = get_object_or_404(Product, slug=slug)
    categories = Category.objects.all()
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        available = request.POST.get('available') == 'on'
        image = request.FILES.get('image')
        
        try:
            # Update product
            product.name = name
            product.category = Category.objects.get(id=category_id)
            product.description = description
            product.price = float(price)
            product.stock = int(stock)
            product.available = available
            
            if image:
                product.image = image
            
            product.slug = slugify(name)
            product.save()
            
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('product_detail', slug=product.slug)
            
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    context = {
        'product': product,
        'categories': categories
    }
    return render(request, 'store/edit_product.html', context)







def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    request.session['buy_now_product'] = product_id
    return redirect("send_otp")

def delete_product(request, slug):
    
    """View for deleting products"""
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('product_list')

    
    context = {
        'product': product
    }
    return render(request, 'store/delete_product.html', context)