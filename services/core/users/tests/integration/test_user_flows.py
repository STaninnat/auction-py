import pytest
from django.urls import reverse
from rest_framework import status

from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserFlows:
    def test_update_profile(self, api_client):
        user = UserFactory(first_name="Old", last_name="Name")
        api_client.force_authenticate(user=user)

        url = reverse("user_me")
        data = {"first_name": "New", "last_name": "Identity"}

        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.first_name == "New"
        assert user.last_name == "Identity"

    def test_change_password(self, api_client):
        user = UserFactory()
        user.set_password("old_password")
        user.save()

        api_client.force_authenticate(user=user)

        url = reverse("change_password")
        data = {"old_password": "old_password", "new_password": "new_strong_password_123"}

        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK

        # Verify new password works
        user.refresh_from_db()
        assert user.check_password("new_strong_password_123")
        assert not user.check_password("old_password")

    def test_change_password_wrong_old(self, api_client):
        user = UserFactory()
        user.set_password("old_password")
        user.save()

        api_client.force_authenticate(user=user)

        url = reverse("change_password")
        data = {"old_password": "wrong_password", "new_password": "new_strong_password_123"}

        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "old_password" in response.data
