import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _ # to make translation easy later on

class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text="Enter a date between now and 4 weeks (default 3 weeks).")

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        # Check if date is not in the past
        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past.'))

        # Check whether date is in allowed 4-week range from today
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead.'))

        # Always remember to return clean, validated data
        return data
