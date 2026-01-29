from django.contrib import admin
from .models import Book, Shelf, UserBook

admin.site.register(Book)
admin.site.register(Shelf)
admin.site.register(UserBook)