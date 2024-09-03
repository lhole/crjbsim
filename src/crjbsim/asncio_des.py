import functools
import logging
import traceback
from asyncio import AbstractEventLoop, AbstractEventLoopPolicy, events, futures, tasks
from concurrent.futures import Future
from typing import Callable, Any, Awaitable

from crjbsim import time_provider
from crjbsim.discrete_event_scheduler import DiscreteEventScheduler, Event

logger = logging.getLogger()


class DiscreteEventLoop(AbstractEventLoop):
    def __init__(self) -> None:
        time_provider.set_time(0)
        self.scheduler = DiscreteEventScheduler()

    def time(self) -> float:
        return time_provider.get_time()

    def call_soon(self, callback: Callable, *args: Any, context=None) -> Event:
        return self.call_later(0, callback, *args, context=context)

    def call_later(self, delay, callback, *args, context=None) -> Event:
        return self.call_at(self.time() + delay, callback, *args, context=context)

    def call_at(self, when, callback: Callable, *args, context=None) -> Event:
        wrapped = functools.partial(callback, *args)
        return self.scheduler.do_at(when, wrapped)

    def run_until_complete(self, future: Awaitable) -> None:
        events._set_running_loop(self)
        future = tasks.ensure_future(future, loop=self)
        self.scheduler.start()
        events._set_running_loop(None)

    def close(self) -> None:
        pass

    def create_future(self) -> futures.Future:
        return futures.Future(loop=self)

    def create_task(self, coro, *, name=None, context=None) -> tasks.Task:
        task = tasks.Task(coro, loop=self, name=name)
        return task

    def get_debug(self) -> bool:
        return False

    def default_exception_handler(self, context) -> None:
        """From BaseEventLoop"""
        message = context.get('message')
        if not message:
            message = 'Unhandled exception in event loop'

        exception = context.get('exception')
        if exception is not None:
            exc_info = (type(exception), exception, exception.__traceback__)
        else:
            exc_info = False

        log_lines = [message]
        for key in sorted(context):
            if key in {'message', 'exception'}:
                continue
            value = context[key]
            if key == 'source_traceback':
                tb = ''.join(traceback.format_list(value))
                value = 'Object created at (most recent call last):\n'
                value += tb.rstrip()
            elif key == 'handle_traceback':
                tb = ''.join(traceback.format_list(value))
                value = 'Handle created at (most recent call last):\n'
                value += tb.rstrip()
            else:
                value = repr(value)
            log_lines.append(f'{key}: {value}')

        logger.error('\n'.join(log_lines), exc_info=exc_info)

    def call_exception_handler(self, context) -> None:
        """From BaseEventLoop"""
        try:
            self.default_exception_handler(context)
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException:
            # Second protection layer for unexpected errors
            # in the default implementation, as well as for subclassed
            # event loops with overloaded "default_exception_handler".
            logger.error('Exception in default exception handler',
                         exc_info=True)

    async def shutdown_asyncgens(self) -> None:
        pass

    async def shutdown_default_executor(self, *args) -> None:
        pass


class DiscreteEventLoopPolicy(AbstractEventLoopPolicy):
    def __init__(self):
        self.loop = None

    def get_child_watcher(self) -> None:
        raise NotImplementedError("DiscreteEventLoopPolicy doesn't support child processes")

    def set_child_watcher(self, watcher) -> None:
        raise NotImplementedError("DiscreteEventLoopPolicy doesn't support child processes")

    def get_event_loop(self) -> DiscreteEventLoop:
        assert self.loop
        return self.loop

    def set_event_loop(self, loop) -> None:
        self.loop = loop

    def new_event_loop(self) -> DiscreteEventLoop:
        return DiscreteEventLoop()
