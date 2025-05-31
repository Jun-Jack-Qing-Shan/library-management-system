from django.contrib import admin
from .models import Author, Book, Genre, ReaderProfile, LoanRecord

# 设置管理后台标题
admin.site.site_header = "图书馆管理系统后台"
admin.site.site_title = "图书馆管理系统"
admin.site.index_title = "欢迎使用图书馆管理系统"

# 图书管理
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'display_genres')
    list_filter = ('status', 'author')
    search_fields = ('title', 'author__name', 'isbn')
    
    # 显示多个分类
    def display_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genre.all()])
    display_genres.short_description = '分类'  # 设置列标题为中文

# 借阅记录管理
class LoanRecordAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'loan_date', 'due_back', 'returned_date', 'status')
    list_filter = ('status', 'borrower__reader_type')
    search_fields = ('book__title', 'borrower__user__username')
    date_hierarchy = 'loan_date'
    
    # 自定义字段显示
    def status(self, obj):
        if obj.returned_date:
            return "已归还"
        elif obj.due_back and obj.due_back < timezone.now().date():
            return "已超期"
        else:
            return "借阅中"
    status.short_description = '状态'  # 设置列标题为中文

# 注册所有模型
admin.site.register(Author)
admin.site.register(Book, BookAdmin)
admin.site.register(Genre)
admin.site.register(ReaderProfile)
admin.site.register(LoanRecord, LoanRecordAdmin)