from django.db import models
from django.urls import reverse
# Create your models here.


class Category(models.Model):
  category_name = models.CharField(max_length=100, unique=True)
  slug = models.SlugField(max_length=100, unique=True)
  description = models.TextField(max_length=255, blank=True)
  category_image = models.ImageField(upload_to='photos/categories', blank=True)

  class Meta:
    verbose_name = 'category'
    verbose_name_plural = 'categories'

  def get_url(self):
    return reverse('shop_by_category', args = [self.slug])

  def __str__(self):
    return self.category_name
class SubCategory(models.Model):
  subcategory_name = models.CharField(max_length=100)
  category = models.ForeignKey(Category, on_delete=models.CASCADE)
  slug = models.SlugField(max_length=100)
  description = models.TextField(max_length=255, blank=True)
  category_image = models.ImageField(upload_to='photos/categories', blank=True)

  class Meta:
    verbose_name = 'subcategory'
    verbose_name_plural = 'subcategories'

  def __str__(self):
    return self.subcategory_name

