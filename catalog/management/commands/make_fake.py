import datetime
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from faker import Faker
from random import randint

from catalog.models import Author, Book, BookInstance, Genre, Language

# Faker.seed(0)
fake = Faker()

"""
Resource:
https://docs.djangoproject.com/en/3.1/howto/custom-management-commands/
"""
class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        return

    def _create_fake_authors(self):
        number_fake_authors = 25
        authors = []
        for i in range(number_fake_authors):
            author = Author.objects.create(
                first_name = fake.first_name(),
                last_name = fake.last_name(),
                date_of_birth = fake.date(),
                date_of_death = fake.date(),
            )
            authors.append(author)
        all_authors = Author.objects.all()

        # Delete fake authors
        for author in authors:
            if author in all_authors:
                author.delete()
                self.stdout.write(self.style.SUCCESS(f'Successfuly deleted {author} record'))

    def _create_fake_users(self):
        simple_profile = fake.simple_profile()
        self.stdout.write(str(simple_profile))

        first_name, last_name = simple_profile['name'].split(' ')
        try:
            user = User.objects.create(
                username=simple_profile['username'],
                password='test',
                first_name=first_name,
                last_name=last_name,
                email=simple_profile['mail']
            )
            user.save()
        except:
            self.stdout.write('exception raised while creating fake user'
                              f' with username {simple_profile["username"]}')

    def _create_languages(self):
        language_set = ['English',
                        'French',
                        'Spanish',
                        'Italian',
                        'German',
                        'Russian',
                        'Korean',
                        'Mandarin',
                        'Japanese',
                        'Thai'
                        ]
        languages = [str(l) for l in Language.objects.all()]
        num_created = 0
        for language in language_set:
            if language not in languages:
                l = Language.objects.create(name=language)
                self.stdout.write(f'added Language({l})')
                num_created += 1
        if num_created == 0:
            self.stdout.write(self.style.SUCCESS(f'No Language objects created.'))
        elif num_created == 1:
            self.stdout.write(self.style.SUCCESS(f'Successfully added {num_created} Language'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully added {num_created} Languages'))

    def _create_fake_books_and_instances(self):
        number_fake_books = 1
        books = []
        authors = Author.objects.all()
        num_authors = authors.count()

        genres = Genre.objects.all()
        num_genres = genres.count()

        languages = Language.objects.all()
        num_languages = languages.count()

        summary = '\n'.join(fake.paragraphs(nb=3))
        for i in range(number_fake_books):
            title = fake.sentence(nb_words=
                random.randint(2, 6)).strip('.').title()
            self.stdout.write(f'Title: {title}')

            author = authors[random.randint(0, num_authors-1)]
            self.stdout.write(f'\tAuthor: {author}')

            summary ='\n'.join(fake.paragraphs(nb=3))
            self.stdout.write(f'\tsummary: {summary}')

            isbn = fake.isbn13()
            self.stdout.write(f'\tisbn13: {isbn}')

            book_genre_count = random.randint(1, num_genres)
            book_genres = [genres[random.randint(0, num_genres-1)] for i in range(book_genre_count)]
            self.stdout.write(f'\tgenres: {book_genres}')

            language = languages[random.randint(0, num_languages-1)]
            self.stdout.write(f'\tlanguage: {language}')

            try:
                book = Book.objects.create(
                    title=title,
                    author=author,
                    summary=summary,
                    isbn=isbn,
                    language=language
                )
                book.genre.set(book_genres)


                self.stdout.write(self.style.SUCCESS(f'Successfully created Book({book})'))
            except:
                self.stdout.write(self.style.ERROR(f'Unable to create Book object'))

    def handle(self, *args, **options):
        # Create fake authors
        # self._create_fake_authors()
        # self._create_fake_users()
        self._create_languages()
        self._create_fake_books_and_instances()


def create_fake_book_instance():
    pass

def create_fake_users():
    pass
