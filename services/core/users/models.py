from common.models import TimestampMixin, UUIDMixin
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(UUIDMixin, TimestampMixin, AbstractUser):
    """
    Custom User Model
    """

    email = models.EmailField(_("email address"), unique=True)

    class Meta:
        db_table = "users"
        verbose_name = _("users")
        verbose_name_plural = _("users")

    def __str__(self) -> str:
        return self.username
