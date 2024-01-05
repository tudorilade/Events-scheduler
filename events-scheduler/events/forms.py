from django import forms
from django.utils import timezone

from events.models import Event


class BaseEventForm(forms.ModelForm):
    """Base Event Form

    A Django Model form inherited by Event Create and Event Update form. The fields are common for both creation and
    updating.
    """
    description = forms.CharField(
        widget=forms.Textarea, max_length=8192, help_text='The description cannot be longer than 8192 characters'
    )

    date = forms.DateTimeField(
        widget=forms.TextInput(attrs={'type': 'datetime-local'}),
        help_text='The date and time of the event'
    )

    class Meta:
        model = Event
        fields = ['title', 'description', 'date']

    def clean_date(self) -> str:
        """
        Method responsible for cleaning the date. An event with a date in the past cannot be created.
        """
        event_date = self.cleaned_data.get('date')

        if event_date < timezone.now():
            self.add_error('date', 'Cannot create events in a past time')

        return event_date


class EventCreateForm(BaseEventForm):
    """Event Create Form

    Child class of BaseEventForm used for creating new users.

    Assumption: users cannot create events in the past
    """
    pass


class EventUpdateForm(BaseEventForm):
    """Event Update Form

    Child class of BaseEventForm used for updating current users.

    Assumption: users cannot modify past events. Once an event has passed, it should remain passed forever.
    """
    def __init__(self, *args, **kwargs):
        """Event update constructor

        Constructor which modifies the behavior of forms field as follows:
            - since all events must have a title, description and date, the user cannot delete info of any field.
            - no user can modify past events. once an event has passed, it should remain as such. all fields are
            disabled

        Even though field is disabled, we make sure by overwriting each clean method to account for changes in
        data is coming from UI. We make sure that no other data is saved (for past events).

        For the time being, we simply return the instance field if we encounter such scenarios.
        """
        super().__init__(*args, **kwargs)

        self.is_past_event = self.instance.date < timezone.now()

        for field in self.fields.values():
            field.disabled = self.is_past_event

    def clean_date(self) -> str:
        event_date = self.cleaned_data.get('date')

        if self.instance.date != event_date and self.is_past_event:
            return self.instance.date

        if event_date < timezone.now():
            self.add_error('date', 'Cannot update events in a past time')

        return event_date

    def clean_title(self) -> str:

        event_title = self.cleaned_data.get('title')

        if self.instance.title != event_title and self.is_past_event:
            return self.instance.title

        return event_title

    def clean_description(self) -> str:

        event_description = self.cleaned_data.get('description')

        if self.instance.title != event_description and self.is_past_event:
            return self.instance.description

        return event_description
