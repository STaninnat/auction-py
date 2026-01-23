import asyncio
import json
import logging
from decimal import Decimal

from auction_service import AuctionService
from config.database import get_db
from config.redis import get_redis
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from utils.auth import AuthenticatedUser, get_current_user
from utils.redis import redis_listener

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/auction/{auction_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    auction_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
):
    """
    WebSocket endpoint for auction real-time updates.
    """
    if user is None:
        await websocket.close()
        return

    # Accept the WebSocket connection
    await websocket.accept()

    logger.info(f"User {user.username} ({user.id}) connected to Auction {auction_id}")

    # Get the channel name
    channel_name = f"auction:{auction_id}"

    # Start Redis Listener (Create a parallel task)
    # We use `asyncio.create_task` to make it run continuously without blocking user messages.
    listener_task = asyncio.create_task(redis_listener(websocket, redis_client, channel_name))

    try:
        auction_service = AuctionService(db)

        # Main loop: receive messages from WebSocket (bid placement)
        while True:
            data = await websocket.receive_text()

            # Process the received message: {"action": "BID", "amount": 100}
            try:
                payload = json.loads(data)
                action = payload.get("action")

                if action == "BID":
                    amount = Decimal(str(payload.get("amount")))

                    # Call service to place bid (Database Lock is handled by service)
                    result = await auction_service.place_bid(
                        auction_id=auction_id,
                        user=user,
                        amount=amount,
                    )

                    if result["success"]:
                        # 1. Send Private ACK to the bidder with their new balance
                        await websocket.send_json(
                            {
                                "type": "BID_ACK",
                                "new_balance": result.get("new_balance"),
                                "amount": result["new_price"],
                                "timestamp": result["timestamp"],
                            }
                        )

                        # 2. Broadcast to Redis channel (Public update)
                        broadcast_msg = json.dumps(
                            {
                                "type": "NEW_BID",
                                "amount": result["new_price"],
                                "bidder": {
                                    "id": str(user.id),
                                    "username": user.username,
                                },
                                "timestamp": result["timestamp"],
                            }
                        )

                        # Publish to Redis channel
                        await redis_client.publish(channel_name, broadcast_msg)

                    else:
                        # Send error message to client (Example: "Bid amount must be greater than current price")
                        await websocket.send_json({"type": "ERROR", "message": result["error"]})

            except json.JSONDecodeError:
                # Skip invalid JSON
                continue
            except Exception as e:
                # Log error and send error message to client
                logger.error(f"Error processing bid: {e}")
                await websocket.send_json({"type": "ERROR", "message": "Internal Error"})

    except WebSocketDisconnect:
        # Log disconnection
        logger.info(f"User {user.username} ({user.id}) disconnected from Auction {auction_id}")
    except Exception as e:
        # Log connection error
        logger.error(f"Connection error: {e}")
    finally:
        # Cancel listener task and close Redis connection
        listener_task.cancel()
        await redis_client.aclose()
