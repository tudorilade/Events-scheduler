from django.urls import path

from users.views import (
    CustomLoginView,
    CustomLogoutView,
    RegisterView,
    ConfirmEmailView,
    UserDetailView,
    UserUpdateView,
    SendConfirmationEmail
)

from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)

urlpatterns = [
    # login / logout
    path('login/', CustomLoginView.as_view(), name='custom_login'),
    path('logout/', CustomLogoutView.as_view(), name='custom_logout'),

    # user related actions
    path('register/', RegisterView.as_view(template_name='registration/register.html'), name='register'),
    path('view/', UserDetailView.as_view(
        template_name='users/view.html'
    ), name='user_view'),
    path('update/', UserUpdateView.as_view(template_name='users/update.html'), name='user_update'),

    # confirm email
    path('confirm/', ConfirmEmailView.as_view(), name='confirm_email'),
    path('confirm-send/', SendConfirmationEmail.as_view(), name='send_confirmation_email'),

    # reset password flow
    path('password-reset/', PasswordResetView.as_view(), name='send_password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete')
]
