from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from events_scheduler.views import HomePageTemplateView

main_urlpatterns = [
    path('', HomePageTemplateView.as_view(template_name='main/home.html'), name='homepage')
]

events_urlpatterns = [
    path('events/', include('events.urls'))
]

users_urlpatterns = [
    path('users/', include('users.urls'))
]

urlpatterns = [
    path('admin/', admin.site.urls)
    ] + main_urlpatterns + events_urlpatterns + users_urlpatterns + \
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
