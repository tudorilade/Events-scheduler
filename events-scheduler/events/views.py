from typing import Dict, Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, Http404, HttpRequest
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View
)

from events.forms import EventCreateForm, EventUpdateForm
from events.models import Event
from events.utils import EventListUserTypeEnum
from events_scheduler.limiters import RateLimitedView
from events_scheduler.utils import unique_slugify


class EventCreateView(RateLimitedView, LoginRequiredMixin, CreateView):
    """Event creation view

    A Django CreateView class with IP-based rate limiting and user authentication. This view is responsible
    for creating new event by the authenticated user.

    Attributes:
        model (Event): The event model that this view operates on.
        form_class (EventCreateForm): The form used for event creation.
    """
    model = Event
    form_class = EventCreateForm

    def form_valid(self, form) -> HttpResponseRedirect:
        """Handles the submission of a valid form

        Method responsible for creating new event if the form is valid and the user is verified.

        Args:
            form (EventCreateForm): a form instance having the validated data
        Returns:
            HttpResponseRedirect: redirect to user_view template
        """
        if not self.request.user.is_verified:
            form.add_error(None, 'User is not verified. Verify your account in order to create events')
            return self.form_invalid(form)

        event = form.save(commit=False)
        event.creator = self.request.user
        event.slug = unique_slugify(event.short_title)
        event.save()
        return super().form_valid(form)

    def get_success_url(self):
        """
        Method responsible for getting the success url when an event is successfully created
        """
        messages.success(
            self.request,
            'The event has been successfully created!'
        )
        return reverse('user_view')


class EventListView(RateLimitedView, ListView):
    """Event List View

    A Django ListView class responsible for listing the events. It has a default pagination of 25 events per page.

    The filtering is done based on two parameters:
        - all
        - creator

    This view renders to events/list.html. It is used for both listing created events to the creator (requested
    user if he or she has events created) and for all users browsing the website.
    This rendering is achieved based on 'all_or_creator' parameter.  

    Based on EventListUserTypeEnum mapping, we determine at dispatch time where to redirect the user according to
    mapping values.
        - all: this returns a queryset with all events to users which browse to "See events"
        - creator: this returns a queryset with all events created by authenticated request user. Moreover,
        authenticated users can edit / delete events only when this endpoint is created. Coresponds to 
        "See created events" section on profile.
    """
    model = Event
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        """Method responsible for determining where to dispatch the request.

        If an invalid parameter has been passed, it will raise Http404 not found. In case the user is not authenticated
        and wants to access events/view/creator endpoint, he or she will be redirected to login page.

        Args:
            request (HttpRequest): the request to dispatch
        Returns:
            redirects to all, creator or login endpoints.
        Raises:
            Http404: 404 not found error in case invalid parameter has been parsed
        """
        all_or_creator = kwargs.get('all_or_creator')
        get_endpoints_mapping = EventListUserTypeEnum.get_mapping()

        if (endpoint := get_endpoints_mapping.get(all_or_creator)) is None:
            raise Http404()

        if not self.request.user.is_authenticated and endpoint == EventListUserTypeEnum.CREATOR:
            messages.info(
                self.request,
                'You have to login first in order to see your events'
            )
            return redirect('custom_login')

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Get queryset

        Method responsible for getting the queryset consisting of all upcoming events according to the endpoint accessed.

        If events/view/creator endpoint is accessed, then it filters according to the requested user.

        Returns:
            qs (QuerySet): a queryset containing the events. The qs is filtered according to requested user when
            the user wants to modify his or her events.
        """
        all_or_creator = EventListUserTypeEnum(self.kwargs.get('all_or_creator'))

        qs = Event.objects.\
            select_related('creator').\
            defer(
                'creator__registration_date', 'creator__first_name', 'creator__last_name', 'creator__password',
                'creator__is_active'
            ).\
            order_by('date')

        match all_or_creator:

            case EventListUserTypeEnum.ALL:
                # we show only upcoming events
                return qs.filter(date__gte=timezone.now())

            case EventListUserTypeEnum.CREATOR if self.request.user.is_authenticated:
                # for detail view from creator perspective, we show all the created events by the user
                return qs.filter(creator=self.request.user)

    def get_context_data(self, *args, object_list=None, **kwargs) -> Dict[str, Any]:
        """Get context data

        Method responsible for returning the context data. Based on the endpoint accessed, show_edit_and_delete flag
        is set accordingly.

        Returns:
            context (Dict): context data containing show_edit_and_delete set on True if /events/view/creator endpoint
            is accessed, thus requested user can modify his or her events. False otherwise.
        """
        context = super().get_context_data()
        all_or_creator = EventListUserTypeEnum(self.kwargs.get('all_or_creator'))

        match all_or_creator:
            case EventListUserTypeEnum.CREATOR:
                show_edit_and_delete = True
            case _:
                show_edit_and_delete = False
        context['show_edit_and_delete'] = show_edit_and_delete
        return context



class EventUpdateView(RateLimitedView, LoginRequiredMixin, UpdateView):
    """Event update view.

    A Django UpdateView with IP-based rate limiting and user authentication. This view is responsible
    for updating existing event instances associated with a user.

    Attributes:
        model: the event model
        form_class: the form used for update events
    """
    model = Event
    form_class = EventUpdateForm

    def get_object(self, queryset=None) -> Event:
        """
        Method responsible for determining the object DetailView manipulates.

        Returns:
            Event: event instance based on slug and authenticated user.
        Raises:
            Http404: 404 not found if requested event record is not found.
        """
        return get_object_or_404(Event, slug=self.kwargs.get('slug'), creator=self.request.user)

    def get_success_url(self) -> str:
        """
        Method responsible for redirecting to event_list upon successful form submission.

        Returns:
            str: The URL to redirect to.

        """
        messages.success(
            self.request,
            'Event successfully updated !'
        )

        return reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.CREATOR.value})


class EventDeleteView(RateLimitedView, LoginRequiredMixin, DeleteView):
    """Event delete view

    A Django DeleteView with IP-based rate limiting and user authentication. This view is responsible
    for deleting existing event instances associated with a user.

    Attributes:
        model: the event model
    """
    model = Event

    def get_object(self, queryset=None) -> Event:
        """
        Method responsible for determining the object DeleteView manipulates.

        Returns:
            Event: event instance based on slug and authenticated user.
        Raises:
            Http404: 404 not found if requested event record is not found.
        """
        return get_object_or_404(Event, slug=self.kwargs.get('slug'), creator=self.request.user)

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Assumption: Events in the past cannot be deleted fron database.

        Method responsible for checking also if the event is in the future. If so, the user cannot delete it.
        """
        event = self.object

        if event.date < timezone.now():
            messages.info(
                self.request,
                'You cannot delete past events'
            )
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Method responsible for redirecting to event_list upon successful deletion.

        Returns:
            str: The URL to redirect to.

        """
        messages.success(
            self.request,
            'Event successfully deleted !'
        )
        return reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.CREATOR.value})


class EventDetailView(RateLimitedView,  DetailView):
    """Event detail view

    A Django DetailView with IP-based rate limiting and user authentication. This view is responsible
    for viewing details of an existing event.

    Attributes:
        model: the event model
    """
    model = Event

    def get_object(self, queryset=None) -> Event:
        """
        Method responsible for setting the object which DetailView is going to display

        Raises:
            Http404: not found if object is not found
        """
        return get_object_or_404(Event, slug=self.kwargs.get('slug'))


    def get_context_data(self, **kwargs):
        """
        Method responsible for populating context data with joined variable.

        Joined variable is set to True when authenticated user has joined to the event. It is set on False
        otherwise. According to this variable, corresponding action is displayed on UI (join/withdraw). If the
        request user is not authenticated, an informative message is displayed on UI which says that only
        authenticated users can join / withdraw from events.
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['joined'] = self.object.participants.filter(id=self.request.user.id).exists()
        return context


@method_decorator(csrf_protect, name='dispatch')
class JoinEvent(RateLimitedView, LoginRequiredMixin, View):
    """Join Event View

    A Django View class with IP-based rate limiter and user authentication required
    responsible for handling join requests to events.

    If requested event is not found, a 404 not found error will be raised.
    """

    def post(self, request,  *args, **kwargs) -> HttpResponseRedirect | Http404:
        """
        Method responsible for handling post request coming via /join endpoint. It handles the following scenarios:
            - if the event is not found, a Http404 is raised
            - if the participant has already joined, we avoid double joining, thus violating unique_together constraint
            - redirects the user to events/view/all endpoint with informative message (including requests when
            the user is already joined)

        Args:
            request (HttpRequest): the http request to handle

        Returns:
            HttpResponseRedirect: redirects to events/view/all

        Raises:
            Http404: http 404 not found error if event is not found
        """
        event_slug = kwargs.get('slug')
        try:
            event = Event.objects.prefetch_related('participants').get(slug=event_slug)
        except Event.DoesNotExist:
            raise Http404()

        # avoid unique_together violation in case the user has already joined to the event
        if not event.participants.filter(id=request.user.id).exists():
            event.participants.add(self.request.user)
            event.update_participants_number()

        messages.success(
            request,
            f'You have successfully joined to event: {event}'
        )

        return HttpResponseRedirect(
            reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.ALL.value})
        )


@method_decorator(csrf_protect, name='dispatch')
class WithdrawEvent(RateLimitedView, LoginRequiredMixin, View):
    """Withdraw Event View

    A Django View class with IP-based rate limiter and user authentication required
    responsible for handling join requests to events.

    If requested event is not found, a 404 not found error will be raised.

    It behaves similar to JoinEvent view.
    """

    def post(self, request, *args, **kwargs):
        """
        Method responsible for handling post request coming via /withdraw endpoint. It handles the following scenarios:
            - if the event is not found, a Http404 is raised
            - if the participant has already withdrawn, we don't remove it once again
            - redirects the user to events/view/all endpoint with informative message (including requests when
            the user is already withdrawn)

        Args:
            request (HttpRequest): the http request to handle

        Returns:
            HttpResponseRedirect: redirects to events/view/all

        Raises:
            Http404: http 404 not found error if event is not found
        """
        event_slug = kwargs.get('slug')
        try:
            event = Event.objects.prefetch_related('participants').get(slug=event_slug)
        except Event.DoesNotExist:
            raise Http404()

        # if the request user is not attending anymore to the event, we don't do anything on db
        if event.participants.filter(id=request.user.id).exists():
            event.participants.remove(self.request.user)
            event.update_participants_number()

        messages.success(
            request,
            f'You have successfully withdrawn from the event: {event}'
        )

        return HttpResponseRedirect(
            reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.ALL.value})
        )
