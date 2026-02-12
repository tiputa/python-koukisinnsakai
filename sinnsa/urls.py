from django.urls import path
from . import views

urlpatterns = [
    path("", views.book_list, name="book_list"),
    path("add/", views.book_add, name="book_add"),
    path("shelves/", views.shelf_list_create, name="shelf_list_create"),
    path("isbn-lookup/", views.isbn_lookup, name="isbn_lookup"),
    path("items/<int:pk>/edit/", views.userbook_edit, name="userbook_edit"),
    path("items/<int:pk>/delete/", views.userbook_delete, name="userbook_delete"),
    path("shelves/<int:shelf_id>/", views.shelf_books, name="shelf_books"),
    path("shelves/uncategorized/", views.shelf_uncategorized, name="shelf_uncategorized"),
]