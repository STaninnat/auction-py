import sentry_sdk
from decouple import config
from fastapi import Depends, FastAPI, WebSocket
from utils.auth import AuthenticatedUser, get_current_user
from utils.logger import LoggerSetup

# Setup Logging
logger_setup = LoggerSetup()
root_logger = logger_setup.configure()

# Setup Sentry
SENTRY_DSN = config("SENTRY_DSN_REALTIME", default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        environment="development" if config("DEBUG", cast=bool) else "production",
    )

# Create FastAPI app
app = FastAPI()


@app.get("/")
async def root():
    root_logger.info("Health check endpoint accessed", extra={"client_ip": "127.0.0.1"})
    return {"message": "Hello form Real-time Service (FastAPI)"}


@app.websocket("/ws/auction/{auction_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    auction_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    WebSocket endpoint for auction real-time updates.
    """
    if user is None:
        return

    # Accept the WebSocket connection
    await websocket.accept()

    root_logger.info(f"User {user.username} ({user.id}) connected to Auction {auction_id}")

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Hello {user.username}, you said: {data}")

    except Exception as e:
        root_logger.info(f"User {user.username} disconnected: {e}")
