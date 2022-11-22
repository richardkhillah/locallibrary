import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from catalog.forms import RenewBookForm
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

class LoanedBookByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing all books on loan to current user"""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'

    paginate_by=10

    def get_queryset(self):
        return BookInstance.objects\
                .filter(borrower=self.request.user)\
                .filter(status__exact='o')\
                .order_by('due_back')

class AllBorrowedListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    permission_required = 'can_mark_returned'
    template_name = 'catalog/all_borrowed_list.html'
    paginate_by=10

    def get_queryset(self):
        return BookInstance.objects\
                .filter(status__exact='o')\
                .order_by('due_back')

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific book instance by a Libraian, or
        any other user with the `can_mark_returned` permission."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request, process Form data
    if request.method == 'POST':
        # Create form instance and bind with request data (user input)
        form = RenewBookForm(request.POST)

        if form.is_valid():
            # Write clean data back to database
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            return HttpResponseRedirect(reverse('all-borrowed'))
    else:
        proposed_renewal_date = \
            datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={
            'renewal_date': proposed_renewal_date
        })

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)

class AuthorCreate(PermissionRequiredMixin, CreateView):
    """For authenticated and permissioned users, create a new Author entry.
        success URL defaults to page displaying new/updated info, here will be:
        'author-detail'
    """
    model = Author
    permission_required = 'can_mark_returned'
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    # initial = {'date_of_death': '11/06/2020'}  # for example of initial data

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    """For authenticated and permissioned users, create a new Author entry
        success URL defaults to page displaying new/updated info, here will be:
        'author-detail'
    """
    model = Author
    permission_required = 'can_mark_returned'
    # fields = '__all__' # BAD Idea. Future model alterations can cause this to be unsafe.
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    """For authenticated and permissioned users, create a new Author entry.
        sucess URL must be specified since record will not exist for
        author-detail.
    """
    model = Author
    permission_required = 'can_mark_returned'
    # Must be overridden
    # Lazy because we're providing a url to a class-based view attribute.
    success_url = reverse_lazy('authors')
