from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from utils.auth import get_current_user


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    """Test that a valid token returns an AuthenticatedUser."""
    token = "valid_token"
    expected_payload = {"user_id": "123", "username": "testuser"}

    mock_websocket = AsyncMock()

    with patch("jwt.decode", return_value=expected_payload):
        user = await get_current_user(mock_websocket, token=token)

        assert user is not None
        assert user.id == "123"
        assert user.username == "testuser"
        mock_websocket.close.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_missing_token():
    """Test that missing token closes the connection."""
    mock_websocket = AsyncMock()

    user = await get_current_user(mock_websocket, token=None)

    assert user is None
    mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test that invalid token (raising exception) closes connection."""
    token = "invalid_token"
    mock_websocket = AsyncMock()

    with patch("jwt.decode", side_effect=Exception("Invalid token")):
        user = await get_current_user(mock_websocket, token=token)

        assert user is None
        mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)


@pytest.mark.asyncio
async def test_get_current_user_missing_user_id():
    """Test that token without user_id is treated as invalid."""
    token = "token_no_id"
    payload = {"username": "testuser"}  # Missing user_id
    mock_websocket = AsyncMock()

    with patch("jwt.decode", return_value=payload):
        user = await get_current_user(mock_websocket, token=token)

        assert user is None
        mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)
