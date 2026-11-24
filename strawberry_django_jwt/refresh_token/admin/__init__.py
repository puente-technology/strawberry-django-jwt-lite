from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from strawberry_django_jwt.refresh_token import models
from strawberry_django_jwt.refresh_token.admin import filters


@admin.register(models.RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "token", "created", "revoked", "is_expired"]
    list_filter = (filters.RevokedFilter, filters.ExpiredFilter)
    raw_id_fields = ("user",)
    search_fields = ("token",)
    actions = ("revoke",)

    @admin.action(description=_("Revoke selected %(verbose_name_plural)s"))
    def revoke(self, request, queryset):
        queryset.update(revoked=timezone.now())

    @admin.display(description=_("is expired"), boolean=True)
    def is_expired(self, obj):
        return obj.is_expired()
