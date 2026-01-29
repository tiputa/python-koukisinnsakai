from django.urls import path
from . import views

urlpatterns = [
    path("", views.book_list, name="book_list"),
    path("add/", views.book_add, name="book_add"),
    path("shelves/", views.shelf_list_create, name="shelf_list_create"),
    path("isbn-lookup/", views.isbn_lookup, name="isbn_lookup"),
    
]