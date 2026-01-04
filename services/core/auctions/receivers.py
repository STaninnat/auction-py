import logging

from django.dispatch import receiver

from .signals import auction_finished
from .tasks import notify_winner_task

logger = logging.getLogger(__name__)


@receiver(auction_finished)
def on_auction_finished(sender=None, auction=None, **kwargs):
    """
    This function will execute immediately after the Signal 'auction_finished' is sent.
    """
    logger.info(f"Signal received! Auction {auction.id} has finished.")

    # Asynchronous task execution
    # .delay() assigns the task to a Worker (the User doesn't have to wait)
    if auction.winner:
        notify_winner_task.delay(auction_id=str(auction.id))
    else:
        logger.info("No winner for this auction. Skipping email task.")
