from django.urls import path
from .views import (
    HomeView, 
    BookListView, 
    BookDetailView, 
    search_books,
    borrow_book,
    return_book,
    my_books,
    register,
    admin_dashboard
)
from django.contrib.auth import views as auth_views
from .views import custom_logout
app_name = 'catalog'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('books/', BookListView.as_view(), name='book-list'),
    path('book/<int:pk>/', BookDetailView.as_view(), name='book-detail'),
    path('search/', search_books, name='search'),
    
    # 认证相关
    path('login/', auth_views.LoginView.as_view(
    template_name='catalog/login.html',
    redirect_authenticated_user=True
), name='login'),
    # 修改登出路径
    path('logout/', custom_logout, name='logout'),
    path('register/', register, name='register'),
    
    # 借阅相关
    path('book/<int:book_id>/borrow/', borrow_book, name='borrow-book'),
    path('loan/<int:loan_id>/return/', return_book, name='return-book'),
    path('my-books/', my_books, name='my-books'),
    
    # 管理员统计面板
    path('dashboard/', admin_dashboard, name='admin-dashboard'),
]