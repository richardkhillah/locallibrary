from django.contrib import admin

from .models import Author, Book, BookInstance, Genre, Language

# Register your models here.
admin.site.register(Genre)
admin.site.register(Language)

class BookInline(admin.TabularInline):
    model = Book

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'date_of_birth', 'date_of_death']
    fields = ['first_name', 'last_name', ('date_of_birth', 'date_of_death')]
    inlines = [BookInline]
"""
insted of using the following to register after AuthorAdmin
admin.site.register(Author, AuthorAdmin)

use the decorator
@admin.register(Author)
class AuthorAdmin(*): ...
"""

class BookInstanceInline(admin.TabularInline):
    model = BookInstance

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'display_genre']
    inlines = [BookInstanceInline]

@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_filter = ('status', 'due_back')

    list_display = ['display_title', 'status', 'borrower', 'due_back', 'id']
    fieldsets = (
        (None, {
            'fields': ('book', 'imprint', 'id')
        }),
        ('Availability', {
            'fields': [('status', 'due_back', 'borrower')]
        })
    )
