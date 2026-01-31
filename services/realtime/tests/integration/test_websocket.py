import json
from unittest.mock import AsyncMock, patch

import pytest
from main import app
from utils.auth import AuthenticatedUser, get_current_user

# Mock Data
MOCK_USER = AuthenticatedUser(id="user_123", username="test_bidder")


async def override_get_current_user():
    return MOCK_USER


@pytest.fixture
def authenticated_client(websocket_client):
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield websocket_client
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_websocket_connect_success(authenticated_client):
    """Test successful WebSocket connection."""
    with authenticated_client.websocket_connect("/ws/auction/auction_1?token=mock_token"):
        # Connection established
        pass


@pytest.mark.asyncio
async def test_websocket_place_bid(authenticated_client, mock_redis):
    """Test placing a bid via WebSocket."""
    auction_id = "auction_abc"

    # Mock AuctionService to return success
    mock_service_instance = AsyncMock()
    mock_service_instance.place_bid.return_value = {
        "success": True,
        "new_price": "150.00",
        "new_balance": "850.00",
        "timestamp": "2023-01-01T12:00:00Z",
    }

    with patch("routers.auction.AuctionService", return_value=mock_service_instance):
        with authenticated_client.websocket_connect(f"/ws/auction/{auction_id}") as websocket:
            # Send BID message
            bid_payload = {"action": "BID", "amount": 150.00}
            websocket.send_json(bid_payload)

            # 1. Expect Private ACK
            response = websocket.receive_json()
            assert response["type"] == "BID_ACK"
            assert response["amount"] == "150.00"
            assert response["new_balance"] == "850.00"

            # 2. Verify Redis Publish (Broadcast)
            # mock_redis fixture is auto-used via dependency_overrides in conftest
            # But we need to access the mock object. It is passed as argument.

            # Wait a bit for the async task that publishes to Redis
            import asyncio

            await asyncio.sleep(0.1)

            mock_redis.publish.assert_called()
            call_args = mock_redis.publish.call_args
            assert call_args[0][0] == f"auction:{auction_id}"

            msg_data = json.loads(call_args[0][1])
            assert msg_data["type"] == "NEW_BID"
            assert msg_data["amount"] == "150.00"
            # masked username for "test_bidder" is "t***r"
            assert msg_data["bidder"]["username"] == "t***r"


@pytest.mark.asyncio
async def test_websocket_place_bid_failure(authenticated_client):
    """Test placing an invalid bid."""
    auction_id = "auction_abc"

    mock_service_instance = AsyncMock()
    mock_service_instance.place_bid.return_value = {"success": False, "error": "Bid too low"}

    with patch("routers.auction.AuctionService", return_value=mock_service_instance):
        with authenticated_client.websocket_connect(f"/ws/auction/{auction_id}") as websocket:
            websocket.send_json({"action": "BID", "amount": 10.00})

            response = websocket.receive_json()
            assert response["type"] == "ERROR"
            assert response["message"] == "Bid too low"
