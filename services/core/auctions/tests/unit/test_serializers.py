from django.test import TestCase
from users.models import User

from auctions.serializers import MaskedUserSummarySerializer


class TestMaskedUserSerializer(TestCase):
    def test_masking_standard_username(self):
        user = User(id="123", username="john_doe")
        serializer = MaskedUserSummarySerializer(user)
        self.assertEqual(serializer.data["username"], "j***e")

    def test_masking_short_username(self):
        user = User(id="123", username="jo")
        serializer = MaskedUserSummarySerializer(user)
        self.assertEqual(serializer.data["username"], "j***")

    def test_masking_empty_username(self):
        user = User(id="123", username="")
        serializer = MaskedUserSummarySerializer(user)
        self.assertEqual(serializer.data["username"], "Anonymous")
