from django.shortcuts import render, get_object_or_404,redirect
from .models import Product
from category.models import Category,SubCategory
from django.http import HttpResponse
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .recomndation import get_recommendations
from urllib.parse import urlencode
from django.contrib import messages



# def product_detail(request, category_slug, product_slug):
#   try:
#     single_product = Product.objects.get(category__slug=category_slug,slug=product_slug)

#   except Exception as e:
#     raise e
#   context = {
#     'single_product': single_product
#   }
#   return render(request, 'product.html', context)

def product_detail(request, category_slug, product_slug):

    single_product = Product.objects.get(
        category__slug=category_slug,
        slug=product_slug
    )

    recommended_products = get_recommendations(single_product.id, 8)

    context = {
        'single_product': single_product,
        'recommended_products': recommended_products,
    }

    return render(request, 'product.html', context)




# def shop(request, category_slug=None):

#     products = Product.objects.filter(is_available=True).order_by('-created_date')

#     if category_slug:
#         category = get_object_or_404(Category, slug=category_slug)
#         products = products.filter(category=category)


#     ### Price range filter
#     min_price = request.GET.get('min_price')
#     max_price = request.GET.get('max_price')
#     if min_price:
#         products = products.filter(price__gte=min_price)
#     if max_price:
#         products = products.filter(price__lte=max_price)

#     ### Upload date filter
#     date = request.GET.get('date')
#     if date:
#         products = products.filter(created_date__date=date)

#     # Pagination
#     paginator = Paginator(products, 2)
#     page = request.GET.get('page')
#     paged_products = paginator.get_page(page)

#     context = {
#         "products": paged_products,
#         "categories": Category.objects.all(),
#     }

#     return render(request, "shop.html", context)

def shop(request, category_slug=None):  
    products = Product.objects.filter(is_available=True).order_by('-created_date')  


    if category_slug:  
        category = get_object_or_404(Category, slug=category_slug)  
        products = products.filter(category=category)

    selected_category = request.GET.get('category')
    if selected_category:
        products = products.filter(category__slug=selected_category) 
    

    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    date = request.GET.get('date', '')
    if date:
        products = products.filter(created_date__date=date)

    
    paginator = Paginator(products, 3)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    query_string = urlencode({
        'category': selected_category or '',
        'min_price': min_price or '',
        'max_price': max_price or '',
        'date': date or '',
    })

    context = {
        "products": paged_products,
        "categories": Category.objects.all(),
        "selected_category": selected_category,
        "min_price": min_price,
        "max_price": max_price,
        "date": date,
        "query_string": query_string
    }

    return render(request, "shop.html", context)

def search(request):

    keyword = request.GET.get('keyword').lower()

    products = []
    recommended_terms = []

    if keyword:
        products = Product.objects.filter(
            Q(product_name__icontains=keyword) |
            Q(description__icontains=keyword) |
            Q(subcategory__subcategory_name__icontains=keyword)
        ).distinct()

        subcategories = SubCategory.objects.filter(
            subcategory_name__icontains=keyword
        ).distinct()


        recommended_terms = [s.subcategory_name for s in subcategories]

        recommended_terms = recommended_terms[:10]

    context = {
        'products': products,
        'recommended_terms': recommended_terms,
    }

    return render(request, 'shop.html', context)

def live_search(request):
    keyword = request.GET.get('keyword', '').lower()

    results = []

    if keyword:
        subcats = SubCategory.objects.filter(
            subcategory_name__icontains=keyword
        )[:10]

        results = [s.subcategory_name for s in subcats]

    return JsonResponse({"suggestions": results})
