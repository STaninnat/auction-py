from django.contrib.auth import get_user_model
from factory import Sequence
from factory.django import DjangoModelFactory

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda n: f"user_{n}")
    email = Sequence(lambda n: f"user_{n}@example.com")
    first_name = "John"
    last_name = "Doe"
    is_active = True
