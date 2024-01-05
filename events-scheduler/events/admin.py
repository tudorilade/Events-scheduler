from django.contrib import admin

from events.models import Event, Participation


class EventAdmin(admin.ModelAdmin):
    """Event Admin

    A Django Admin model representing the events in admin dashboard.
    """
    list_display = ('title', 'date', 'number_of_participants')

    def number_of_participants(self, obj):
        return obj.participants.all().count()

    number_of_participants.short_description = 'Number of participants'


class ParticipationAdmin(admin.ModelAdmin):
    """Participation Admin

    A Django Admin model representing the intermediary table between events and users.
    """

    list_display = ('event', 'participant')


admin.site.register(Event, EventAdmin)
admin.site.register(Participation, ParticipationAdmin)
