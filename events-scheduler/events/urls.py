from django.urls import path

from events.views import (
    EventCreateView,
    EventDeleteView,
    EventDetailView,
    EventListView,
    EventUpdateView,
    JoinEvent,
    WithdrawEvent
)

urlpatterns = [
    path('create/', EventCreateView.as_view(template_name='events/create.html'), name='event_create'),
    path('view/<str:all_or_creator>', EventListView.as_view(template_name='events/list.html'), name='event_list'),
    path('update/<slug:slug>', EventUpdateView.as_view(template_name='events/update.html'), name='event_update'),
    path('delete/<slug:slug>', EventDeleteView.as_view(template_name='events/delete.html'), name='event_delete'),
    path('detail/<slug:slug>', EventDetailView.as_view(template_name='events/detail.html'), name='event_detail'),
    path('join/<slug:slug>', JoinEvent.as_view(), name='event_join'),
    path('withdraw/<slug:slug>', WithdrawEvent.as_view(), name='event_withdraw')
]
