import logging

from fastapi import WebSocket
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


async def redis_listener(
    websocket: WebSocket,
    redis_client: Redis,
    channel_name: str,
):
    """
    Redis listener for auction real-time updates. Forward to WebSocket (background task).
    """

    # Subscribe to the channel
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel_name)

    try:
        # Listen for messages
        async for message in pubsub.listen():
            if message["type"] == "message":
                # Forward the message to the WebSocket
                data = message["data"].decode("utf-8")
                await websocket.send_text(data)

    except Exception as e:
        logger.error(f"Error in redis_listener: {e}")
    finally:
        # Unsubscribe and close the connection
        await pubsub.unsubscribe(channel_name)
        await pubsub.aclose()
