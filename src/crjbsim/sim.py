import random

from crjbsim import des_aware_logging, time_provider
from crjbsim.discrete_event_scheduler import DiscreteEventScheduler


scheduler = None


def run_sim(initial_event, post_processing=None) -> None:
    random.seed(0)
    des_aware_logging.setup()
    time_provider.set_time(0)

    global scheduler
    scheduler = DiscreteEventScheduler()

    scheduler.do_in(0, initial_event)

    scheduler.start()

    if post_processing:
        post_processing()
