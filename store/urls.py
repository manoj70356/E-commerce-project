from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.shop, name='shop'),
    path('category/<slug:category_slug>/', views.shop, name='shop_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='shop_by_category'),
    path('live-search/', views.live_search, name='live_search'),
    path('search/', views.search, name='search'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)