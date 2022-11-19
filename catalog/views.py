from django.shortcuts import render
from django.views import generic

from .models import Book, Author, BookInstance, Genre

# Create your views here.
def index(request):
    """View the home page"""
    # Generate counts for some objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Availabile books (status == 'a')
    num_instances_available = \
        BookInstance.objects.filter(status__exact='a').count()

    num_authors = Author.objects.count()    # all() implicit

    # Challenge
    num_genres = Genre.objects.count()

    num_harry_potter_books = Book.objects.filter(title__icontains='Harry Potter').count()

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'num_harry_potter_books': num_harry_potter_books,
        'num_visits': num_visits,
    }

    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    model = Book
    paginate_by = 5

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 5

class AuthorDetailView(generic.DetailView):
    model = Author
