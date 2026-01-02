from django.shortcuts import render
from store.models import Product
from category.models import Category

def home(request):
    products = Product.objects.filter(is_available=True)
    newaly_add = Product.objects.order_by('-created_date')[:4]
    categories = Category.objects.all() 
    context = {
        'products': products,
        'categories': categories,
        'newaly_add': newaly_add
    }
    return render(request, 'index.html', context)