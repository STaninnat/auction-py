import logging
import time

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import AuctionListing

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def notify_winner_task(self, auction_id: str):
    """
    Task for sending email notifications to winners (running in the background).
    bind=True: To allow access to the task instance (e.g., self.retry)
    max_retries=3: Allows 3 attempts if the task fails
    """
    try:
        # Simulate email sending process
        logger.info(f"Starting email task for Auction ID: {auction_id}.")
        time.sleep(5)

        # Retrieving the actual data (This comment will be enabled in the future for actual sending).
        # auction = AuctionListing.objects.get(id=auction_id)
        # if auction.winner:
        #     logger.info(f"Sending email to {auction.winner.email}...")
        #     send_mail(
        #         subject="You won the auction!",
        #         message="Congratulations! You have won the auction.",
        #         from_email="from@example.com",
        #         recipient_list=[auction.winner.email],
        #     )
        logger.info(f"Email sent successfully for Auction {auction_id}.")
        return "Email Sent Successfully"

    except Exception as exc:
        logger.error(f"Failed to send email for Auction {auction_id}: {exc}")
        raise self.retry(exc=exc, countdown=60) from exc


@shared_task
def check_and_close_expired_auctions():
    """
    Task for checking and closing expired auctions (running in the background every 1 minute).
    """

    now = timezone.now()

    with transaction.atomic():
        expired_auctions = AuctionListing.objects.select_for_update().filter(
            status=AuctionListing.Status.ACTIVE,
            end_time__lt=now,
        )

        count = 0
        for auction in expired_auctions:
            if auction.current_price > auction.starting_price:
                auction.status = AuctionListing.Status.FINISHED
                notify_winner_task.delay(auction.id)
            else:
                auction.status = AuctionListing.Status.EXPIRED

            auction.save()
            count += 1

    logger.info(f"Closed {count} expired auctions.")

    return f"Closed {count} expired auctions."
