from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Book, Author, Genre, ReaderProfile, LoanRecord
from django.contrib.auth import logout as auth_logout

def custom_logout(request):
    auth_logout(request)
    messages.info(request, "您已成功退出登录")
    return redirect('catalog:login')
class HomeView(TemplateView):
    template_name = 'catalog/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book_count'] = Book.objects.count()
        context['author_count'] = Author.objects.count()
        return context

class BookListView(ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'books'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = super().get_queryset()
        genre_id = self.request.GET.get('genre')
        if genre_id:
            queryset = queryset.filter(genre__id=genre_id)
        return queryset.order_by('title')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genres'] = Genre.objects.all()
        context['selected_genre'] = int(self.request.GET.get('genre', 0))
        return context

class BookDetailView(DetailView):
    model = Book
    template_name = 'catalog/book_detail.html'
    context_object_name = 'book'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['loan_records'] = LoanRecord.objects.filter(book=self.object)[:5]
        return context

def search_books(request):
    query = request.GET.get('q', '')
    books = Book.objects.all()
    
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__name__icontains=query) |
            Q(isbn__icontains=query) |
            Q(summary__icontains=query)
        )
    
    context = {
        'books': books,
        'query': query
    }
    return render(request, 'catalog/search_results.html', context)

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']
        email = request.POST.get('email', '')
        
        # 简单验证
        if password != password2:
            return render(request, 'catalog/register.html', {'error': '两次密码不一致'})
        
        if User.objects.filter(username=username).exists():
            return render(request, 'catalog/register.html', {'error': '用户名已存在'})
        
        # 创建用户
        user = User.objects.create_user(username=username, password=password, email=email)
        
        # 确保创建 ReaderProfile
        ReaderProfile.objects.create(user=user, reader_type='s')
        
        # 自动登录
        user = authenticate(username=username, password=password)
        login(request, user)
        
        return redirect('catalog:home')
    
    return render(request, 'catalog/register.html')

@login_required
def borrow_book(request, book_id):
    # 确保用户有 ReaderProfile
    if not hasattr(request.user, 'readerprofile'):
        ReaderProfile.objects.create(user=request.user, reader_type='s')
    
    reader = request.user.readerprofile
    book = get_object_or_404(Book, pk=book_id)
    
    # 检查图书是否可借
    if book.status != 'a':
        messages.error(request, "这本书当前不可借")
        return redirect('catalog:book-detail', book_id=book.id)
    
    # 检查读者是否达到借书上限
    current_loans = LoanRecord.objects.filter(borrower=reader, returned_date__isnull=True).count()
    if current_loans >= reader.max_books:
        messages.error(request, "您已达到借书上限")
        return redirect('catalog:book-detail', book_id=book.id)
    
    # 计算应还日期
    loan_period = {
        's': 28,  # 学生28天
        't': 90,  # 老师90天
        'l': 365  # 馆员365天
    }
    due_back = timezone.now().date() + timedelta(days=loan_period.get(reader.reader_type, 28))
    
    # 创建借书记录
    LoanRecord.objects.create(
        book=book,
        borrower=reader,
        loan_date=timezone.now(),
        due_back=due_back,
        status='o'
    )
    
    # 更新图书状态
    book.status = 'o'  # 已借出
    book.save()
    
    messages.success(request, f"成功借阅《{book.title}》，请于{due_back}前归还")
    return redirect('catalog:my-books')

@login_required
def return_book(request, loan_id):
    # 确保用户有 ReaderProfile
    if not hasattr(request.user, 'readerprofile'):
        ReaderProfile.objects.create(user=request.user, reader_type='s')
    
    reader = request.user.readerprofile
    loan = get_object_or_404(LoanRecord, pk=loan_id, borrower=reader)
    
    # 确保图书尚未归还
    if loan.returned_date:
        messages.error(request, "这本书已经归还过了")
        return redirect('catalog:my-books')
    
    # 更新借书记录
    loan.returned_date = timezone.now()
    loan.status = 'r'  # 已归还
    loan.save()
    
    # 更新图书状态
    book = loan.book
    book.status = 'a'  # 在馆可借
    book.save()
    
    messages.success(request, f"成功归还《{book.title}》")
    return redirect('catalog:my-books')

@login_required
def my_books(request):
    # 确保用户有 ReaderProfile
    if not hasattr(request.user, 'readerprofile'):
        ReaderProfile.objects.create(user=request.user, reader_type='s')
    
    reader = request.user.readerprofile
    current_loans = LoanRecord.objects.filter(
        borrower=reader, 
        returned_date__isnull=True
    ).order_by('due_back')
    
    past_loans = LoanRecord.objects.filter(
        borrower=reader, 
        returned_date__isnull=False
    ).order_by('-loan_date')[:10]
    
    context = {
        'current_loans': current_loans,
        'past_loans': past_loans
    }
    return render(request, 'catalog/my_books.html', context)

@staff_member_required
def admin_dashboard(request):
    # 确保只有管理员可以访问
    if not request.user.is_staff:
        return redirect('catalog:home')
    
    # 基本统计
    total_books = Book.objects.count()
    available_books = Book.objects.filter(status='a').count()
    borrowed_books = Book.objects.filter(status='o').count()
    total_loans = LoanRecord.objects.count()
    active_loans = LoanRecord.objects.filter(returned_date__isnull=True).count()
    overdue_loans = LoanRecord.objects.filter(
        returned_date__isnull=True, 
        due_back__lt=timezone.now().date()
    ).count()
    
    # 最近借阅
    recent_loans = LoanRecord.objects.order_by('-loan_date')[:10]
    
    context = {
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'total_loans': total_loans,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'recent_loans': recent_loans
    }
    return render(request, 'catalog/admin_dashboard.html', context)

# 添加在 views.py 文件最底部

from django.contrib.auth import logout as auth_logout
from django.contrib import messages

def custom_logout(request):
    # 执行登出操作
    auth_logout(request)
    # 添加一条消息
    messages.info(request, "您已成功退出登录")
    # 重定向到登录页面
    return redirect('catalog:login')