from django.db import models

from users.models import User


class Event(models.Model):
    """Event model

    An event model responsible for storing information about events. One instance represents one record in database.

    Attributes:
        slug (str): slug field to identify the event
        title (str): title of the event
        description (str): the description of the event
        date (str): date when the event will take place
        participants (m2m): Many-to-Many relation ship with users. One user can attend to multiple events. Multiple
        events can be attended by the same user.
        creator (User): creator of the event (User). A creator can join / withdraw from its own event. If he or she
        is the creator, it does not necessarily imply that will always join.
        participants_count (int): number of participants attending the event
    """
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=256)
    description = models.CharField(max_length=8192)
    date = models.DateTimeField(db_index=True)
    participants = models.ManyToManyField(
        User,
        through='Participation',
        related_name='participated_events',
        db_index=True
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_events',
        db_index=True
    )
    participants_count = models.IntegerField(default=0)

    def __str__(self) -> str:
        """
        Magic method responsible for displaying the event as its title
        """
        return f'{self.title}'

    @property
    def short_title(self) -> str:
        """
        Getter responsible for getting a shorter version of the title. Truncated to 50 characters.
        """
        return f'{self.title[:50]}...'

    @property
    def short_description(self) -> str:
        """
        Getter responsible for getting a shorter version of the description. Truncated to 50 characters.
        """
        return f'{self.description[:50]}...'

    def update_participants_number(self):
        """
        Method responsible for updating the participate_count whenever a user joins / withdraws from the event.
        """
        self.participants_count = len(self.participants.all())
        self.save(update_fields=['participants_count'])


class Participation(models.Model):
    """Participation model

    Participation is a model used as intermediary table between event and user (participants). I opted for a custom
    intermediary model because this model can easily be extended with extra fields in feature could be useful.

    Attributes:
        event (Event): foreign key to an event
        participant (User): foreign key to a user

    It translates to: a participant X takes part in event Y.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    participant = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        """
        Meta class used for enforcing uniqueness between event, participant. Thus, same participant cannot
        join to the same event 2 times.
        """
        unique_together = ('event', 'participant')
