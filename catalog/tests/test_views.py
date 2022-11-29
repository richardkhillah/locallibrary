import datetime
import uuid

from django.contrib.auth.models import User # required to assign User as a borrower
from django.contrib.auth.models import Permission # required to assign permission to set book returned
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Author, BookInstance, Book, Genre, Language

class AuthorListViewTest(TestCase):
    @classmethod
    def setUp(self):
        # Create 13 authors for pagination tests
        number_of_authors = 13
        for author_id in range(number_of_authors):
            Author.objects.create(
                first_name=f'Dominique {author_id}',
                last_name=f'Surname {author_id}',
            )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/catalog/authors/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEqual(len(response.context['author_list']), 5)

    def test_list_all_authors(self):
        # Get third page and confirm it has (exactly) remaining 3 items
        response = self.client.get(reverse('authors')+'?page=3')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertEqual(len(response.context['author_list']), 3)

class LoanedBookInstancesByUserListViewTest(TestCase):
    def setUp(self):
        # Create two users
        test_user1 = User.objects.create_user(
            username='testuser1',
            password='1X<ISRUkw+tuK'
        )
        test_user2 = User.objects.create_user(
            username='testuser2',
            password='2HJ1vRV0Z&3iD'
        )

        test_user1.save()
        test_user2.save()

        # Create a book
        test_author = Author.objects.create( first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title',
            summary='My book summary.',
            author=test_author,
            language=test_language,
        )

        # Create genre as a post set
        genre_objects_for_book = Genre.objects.all()
        # direct assignmnet of many-to-many not allowed
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        # Create 30 BookInstance objects
        number_of_book_copies = 30
        for book_copy in range(number_of_book_copies):
            return_date = timezone.localtime() +\
                            datetime.timedelta(days=book_copy%5)
            the_borrower = test_user1 if book_copy%2 else test_user2
            status = 'm'
            BookInstance.objects.create(
                book=test_book,
                imprint='Unlikely Imprint, 2022',
                due_back=return_date,
                borrower=the_borrower,
                status=status,
            )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(response, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Check we used the correct Template
        self.assertTemplateUsed(response, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check we got a reponse "success"
        self.assertTrue(response.status_code, 200)

        # Check that initially we don't have any books in list (none on-loan)
        self.assertTrue('bookinstance_list' in response.context)
        self.assertEqual(len(response.context['bookinstance_list']), 0)

        # Now, change all the books to be on loan
        books = BookInstance.objects.all()[:10]
        for book in books:
            book.status = 'o'
            book.save()

        # Check that now we have borroed books in the list
        response = self.client.get(reverse('my-borrowed'))
        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check we got a reponse "success"
        self.assertTrue(response.status_code, 200)

        # Confirm all books belong to testuser1 and all are on-loan
        for bookitem in response.context['bookinstance_list']:
            self.assertEqual(response.context['user'], bookitem.borrower)
            self.assertEqual(bookitem.status, 'o')

    def test_pages_ordered_by_due_date(self):
        for book in BookInstance.objects.all():
            book.status = 'o'
            book.save()

        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check we got a reponse "success"
        self.assertTrue(response.status_code, 200)

        # Confirm that of the items, only 10 are displayed due to pagination
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertTrue('bookinstance_list' in response.context)
        self.assertEqual(len(response.context['bookinstance_list']), 10)

        last_date = 0
        for book in response.context['bookinstance_list']:
            if last_date == 0:
                last_date = book.due_back
            else:
                self.assertTrue(last_date <= book.due_back)
                last_date = book.due_back

class RenewBookInstancesViewTest(TestCase):
    def setUp(self):
        # create 2 users & save
        test_user1 = User.objects.create_user(
            username='testuser1',
            password='1X<ISRUkw+tuK'
        )
        test_user2 = User.objects.create_user(
            username='testuser2',
            password='2HJ1vRV0Z&3iD'
        )

        test_user1.save()
        test_user2.save()

        # Give testuser2 permissoin to renew book
        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        # Create a book
        test_author = Author.objects.create( first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title',
            summary='My book summary.',
            isbn="ABCDEFG",
            author=test_author,
            language=test_language,
        )

        # Create genre as a post set
        genre_objects_for_book = Genre.objects.all()
        # direct assignmnet of many-to-many not allowed
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        # Create a BookInstance Object for testuser1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        status='o'
        self.test_bookinstance1 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2022',
            due_back=return_date,
            borrower=test_user1,
            status=status,
        )

        # Create BookInstanceObject for testuser2
        self.test_bookinstance2 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2022',
            due_back=return_date,
            borrower=test_user2,
            status=status,
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('renew-book-librarian', \
                        kwargs={'pk': self.test_bookinstance1.pk}))
        # Manually check redirect (Can't use assertRedirect because the redirect is unpredictable)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_forbidden_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username='testuser1',password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('renew-book-librarian', \
                        kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(response.status_code, 403)

    def test_logged_in_with_permission_borrowed_book(self):
        login = self.client.login(username='testuser2',password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-book-librarian', \
                        kwargs={'pk': self.test_bookinstance2.pk}))
        # Check that we are logged in && have right permission
        self.assertEqual(response.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        login = self.client.login(username='testuser2',password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-book-librarian', \
                        kwargs={'pk': self.test_bookinstance1.pk}))
        # Check that we are logged in && have right permission
        self.assertEqual(response.status_code, 200)

    def test_HTTTP404_for_invalid_book_if_logged_in(self):
        # Unlikely UID to match our bookinstance
        test_uuid = uuid.uuid4()
        login = self.client.login(username='testuser2',password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-book-librarian', \
                        kwargs={'pk': test_uuid}))
        # Check that we get the error for a book that doesn't exist
        self.assertEqual(response.status_code, 404)

    def test_uses_correct_template(self):
        login = self.client.login(username='testuser2',password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-book-librarian', \
                        kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/book_renew_librarian.html')

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        login = self.client.login(username='testuser2',password='2HJ1vRV0Z&3iD')
        response = self.client.get(reverse('renew-book-librarian', \
                        kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(response.status_code, 200)

        date_3_weeks_in_future = datetime.date.today()+datetime.timedelta(weeks=3)
        self.assertEqual(response.context['form'].initial['renewal_date'],\
                        date_3_weeks_in_future)


    # TODO: GET THIS TO PASS
    def test_redirects_to_all_borrowed_book_list_on_success(self):
        login = self.client.login(username='testuser2',password='2HJ1vRV0Z&3iD')
# https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Testing
        valid_date_in_future = datetime.date.today()+datetime.timedelta(weeks=2)
        response = self.client.post(reverse('renew-book-librarian', \
                        kwargs={'pk': self.test_bookinstance1.pk}), \
                        {'renewal_date': valid_date_in_future})
        self.assertRedirects(response, reverse('all-borrowed'))

    def test_form_invalid_renewal_date_in_past(self):
        login = self.client.login(username='testuser2',password='2HJ1vRV0Z&3iD')
        date_in_past = datetime.date.today()-datetime.timedelta(weeks=1)
        response = self.client.post(reverse('renew-book-librarian', \
                        kwargs={'pk': self.test_bookinstance1.pk}), \
                        {'renewal_date': date_in_past})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'renewal_date', 'Invalid date - renewal in past.')

    def test_form_invalid_renewal_date_in_future(self):
        login = self.client.login(username='testuser2',password='2HJ1vRV0Z&3iD')
        invalid_date_in_future = datetime.date.today()+datetime.timedelta(weeks=5)
        response = self.client.post(reverse('renew-book-librarian', \
                        kwargs={'pk': self.test_bookinstance1.pk}), \
                        {'renewal_date': invalid_date_in_future})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'renewal_date', 'Invalid date - renewal more than 4 weeks ahead.')






    pass
