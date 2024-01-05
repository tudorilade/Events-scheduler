from django.contrib import admin

from users.models import User, UserVerification


class UserAdmin(admin.ModelAdmin):
    """User Admin

    Admin model responsible for displaying users in admin dashboard.
    """
    list_display = ('email', 'is_verified')

    def is_verified(self, obj):
        return obj.is_verified

    is_verified.short_description = 'User verified'


class UserVerificationAdmin(admin.ModelAdmin):
    """User Verification Admin

    Admin model responsible for displaying UserVerification model in admin dashboard.
    """

    list_display = ('id', 'user')

    def user(self, obj):
        return obj.user

    user.short_description = 'User'


admin.site.register(User, UserAdmin)
admin.site.register(UserVerification, UserVerificationAdmin)
