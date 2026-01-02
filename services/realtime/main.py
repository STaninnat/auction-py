import sentry_sdk
from decouple import config
from fastapi import FastAPI
from utils.logger import LoggerSetup

# Setup Logging
logger_setup = LoggerSetup()
root_logger = logger_setup.configure()

# Setup Sentry
SENTRY_DSN = config("SENTRY_DSN", default=None)
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
