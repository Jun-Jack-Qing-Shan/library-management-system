from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Author(models.Model):
    name = models.CharField(max_length=100, verbose_name='姓名')
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='出生日期')
    date_of_death = models.DateField('逝世日期', null=True, blank=True)
    bio = models.TextField(max_length=1000, blank=True, verbose_name='简介')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '作者'  # 单数名称
        verbose_name_plural = '作者'  # 复数名称

class Genre(models.Model):
    name = models.CharField(max_length=200, help_text='输入图书分类 (如: 科幻, 历史, 编程...)', verbose_name='名称')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '图书分类'
        verbose_name_plural = '图书分类'

class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name='书名')
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作者')
    isbn = models.CharField('ISBN', max_length=13, unique=True, help_text='13位 ISBN号')
    summary = models.TextField(max_length=1000, blank=True, verbose_name='摘要')
    cover = models.ImageField(upload_to='book_covers/', null=True, blank=True, verbose_name='封面')
    
    # 图书状态选项
    STATUS_CHOICES = (
        ('a', '在馆可借'),
        ('r', '已预订'),
        ('o', '已借出'),
        ('c', '仅供阅览'),
        ('m', '维护中'),
    )
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='a',
        blank=True,
        verbose_name='状态',
        help_text='图书当前状态',
    )
    
    genre = models.ManyToManyField(Genre, blank=True, verbose_name='分类', help_text='选择本书所属分类')
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = '图书'
        verbose_name_plural = '图书'

class ReaderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户账号')
    
    # 读者类型选项
    READER_TYPE_CHOICES = (
        ('s', '学生'),
        ('t', '教师'),
        ('l', '馆员'),
    )
    reader_type = models.CharField(
        max_length=1,
        choices=READER_TYPE_CHOICES,
        default='s',
        verbose_name='读者类型'
    )
    
    student_id = models.CharField('学号/工号', max_length=20, unique=True, blank=True, null=True)
    phone_number = models.CharField('联系电话', max_length=15, blank=True)
    max_books = models.PositiveSmallIntegerField('最大可借数', default=5)
    
    def __str__(self):
        return f'{self.user.username} 的档案'
    
    class Meta:
        verbose_name = '读者档案'
        verbose_name_plural = '读者档案'

class LoanRecord(models.Model):
    book = models.ForeignKey(Book, on_delete=models.RESTRICT, verbose_name='所借图书')
    borrower = models.ForeignKey(ReaderProfile, on_delete=models.CASCADE, verbose_name='借阅人')
    loan_date = models.DateTimeField('借出日期', default=timezone.now)
    due_back = models.DateField('应还日期', null=True, blank=True)
    returned_date = models.DateField('归还日期', null=True, blank=True)
    
    # 借阅状态选项
    LOAN_STATUS = (
        ('o', '借阅中'),
        ('r', '已归还'),
        ('l', '已超期'),
    )
    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        default='o',
        blank=True,
        verbose_name='借阅状态',
        help_text='当前借阅状态'
    )
    
    @property
    def is_overdue(self):
        if self.due_back and self.returned_date is None:
            return timezone.now().date() > self.due_back
        return False
    
    def __str__(self):
        return f'{self.book.title} - 借阅人: {self.borrower.user.username}'
    
    class Meta:
        verbose_name = '借阅记录'
        verbose_name_plural = '借阅记录'
        ordering = ['-loan_date']