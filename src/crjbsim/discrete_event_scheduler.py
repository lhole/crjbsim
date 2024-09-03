import logging
from asyncio import TimerHandle
from datetime import timedelta
from typing import Callable

from crjbsim import time_provider

logger = logging.getLogger(__name__)


class EventQueue:
    def __init__(self) -> None:
        self._events: set[Event] = set()

    def pop_next(self) -> "Event":
        """Pop the next event from the queue."""
        # TODO: change to store sorted
        next_event = min(self._events, key=lambda event: event.time)
        self._events.remove(next_event)
        return next_event

    def add(self, event: "Event") -> None:
        """Add an event to the queue."""
        self._events.add(event)

    def __bool__(self) -> bool:
        return bool(self._events)

    def __len__(self) -> int:
        return len(self._events)


class Event(TimerHandle):
    def __init__(self, time: float, runnable: Callable) -> None:
        self.time = time
        self.runnable = runnable
        self._cancelled = False

    def execute(self) -> None:
        """Execute the event."""
        if not self.cancelled():
            self.runnable()

    def cancel(self) -> None:
        """Cancel the event."""
        self._cancelled = True

    def __repr__(self) -> str:
        return f"Event({self.time}, {self.runnable})"

    def cancelled(self) -> bool:
        return self._cancelled

    def __hash__(self) -> int:
        return hash(self.time)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return NotImplemented
        return self.time == other.time and self.runnable == other.runnable


class DiscreteEventScheduler:
    def __init__(self) -> None:
        self._events = EventQueue()

    def start(self) -> None:
        """Start the event loop."""
        while self._events:
            event = self._events.pop_next()
            assert event.time >= time_provider.get_time()
            time_provider.set_time(event.time)
            logger.debug(f"Executing event {event}")
            event.execute()

    def do_at(self, time: float, runnable: Callable) -> Event:
        """Schedule a runnable to be executed at a specific time."""
        event = Event(time, runnable)
        self._events.add(event)
        return event

    def do_in(self, time_delta: float, runnable: Callable) -> Event:
        """Schedule a runnable to be executed in the future."""
        return self.do_at(time_provider.get_time() + time_delta, runnable)
