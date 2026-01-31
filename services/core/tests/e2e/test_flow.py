import json

import httpx
import pytest
import websockets
from django.conf import settings

# Configuration
CORE_URL = "http://localhost:8000"  # Localhost inside the container
REALTIME_WS_URL = "ws://realtime:8000"  # Service name in docker-compose


@pytest.mark.asyncio
async def test_full_auction_flow():
    """
    E2E Test (Client Side):
    1. Login (seeded user)
    2. Fetch Auction ID (seeded auction)
    3. Connect WebSocket
    4. Place Bid -> Verify Broadcast
    5. Logout
    """

    # Client for HTTP requests (Core)
    async with httpx.AsyncClient(base_url=CORE_URL) as client:
        # --- 0. PRE-FETCH CSRF ---
        # Hit admin login page to get a CSRF cookie
        await client.get("/admin/login/")

        # --- 1. LOGIN ---
        # User 'e2e_bidder' is created by 'seed_e2e' command before test runs
        login_data = {"username": "e2e_bidder", "password": "StrongPassword123!"}
        resp = await client.post("/api/auth/login/", json=login_data)
        assert resp.status_code == 200, f"Login failed: {resp.text}"

        # Extract Cookie/Token
        access_token = resp.cookies.get(settings.AUTH_COOKIE)
        assert access_token, "Access token cookie not found"

        # --- 2. GET AUCTION ID ---
        # Fetch list of active auctions to find the one we seeded
        resp = await client.get("/api/auctions/")
        assert resp.status_code == 200

        data = resp.json()
        results = data.get("results", []) if isinstance(data, dict) else data
        e2e_auction = next((a for a in results if a["product"]["title"] == "E2E Product"), None)
        assert e2e_auction is not None, "Seeded E2E Auction not found in list"

        auction_id = e2e_auction["id"]

        # --- 3. CONNECT WEBSOCKET ---
        ws_url = f"{REALTIME_WS_URL}/ws/auction/{auction_id}?token={access_token}"

        async with websockets.connect(ws_url) as websocket:
            # --- 4. PLACE BID ---
            # Bid higher than current (10.00)
            bid_amount = 20.00
            bid_payload = {"action": "BID", "amount": bid_amount}
            await websocket.send(json.dumps(bid_payload))

            # Expect ACK (Private)
            ack_msg = await websocket.recv()
            ack_data = json.loads(ack_msg)
            # Add explicit assertion message if key is missing or type is error
            if ack_data.get("type") == "ERROR":
                pytest.fail(f"Bid failed with error: {ack_data.get('message', 'Unknown Error')}")

            assert ack_data["type"] == "BID_ACK"
            assert float(ack_data["amount"]) == bid_amount

            # Expect BROADCAST (Public)
            # Since we are the only one, we get it immediately
            broadcast_msg = await websocket.recv()
            broadcast_data = json.loads(broadcast_msg)
            assert broadcast_data["type"] == "NEW_BID"
            assert float(broadcast_data["amount"]) == bid_amount
            assert broadcast_data["bidder"]["username"] == "e***r"

            # --- 5. LOGOUT ---
            # Need CSRF token for logout if using cookies
            csrf_token = client.cookies.get("csrftoken")
            assert csrf_token, "CSRF Token cookie not found! Login view might not have set it."

            headers = {"X-CSRFToken": csrf_token, "Referer": CORE_URL, "Origin": CORE_URL}

            resp = await client.post("/api/auth/logout/", headers=headers)
            assert resp.status_code == 205

            # Verify deletion in client cookies
            assert not client.cookies.get(settings.AUTH_COOKIE), "Access token cookie should be cleared"
