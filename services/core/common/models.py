import uuid

from django.db import models


class UUIDMixin(models.Model):
    """
    Mixin to convert Primary Key to UUID (more secure than Auto-increment ID)
    Prevents ID guessing (Insecure Direct Object References - IDOR)
    """

    id: models.UUIDField = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampMixin(models.Model):
    """
    Mixin for automatic creation and editing time logging (Basic Audit Trail)
    """

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
