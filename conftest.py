import asyncio
import logging
from contextlib import suppress

import pytest

logger = logging.getLogger()


def exception_handler(_, context):
    logger.exception(context)


@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop

    Implements gracefully cleaning up asyncio tasks.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    loop.set_exception_handler(exception_handler)
    yield loop
    print("Gathering tasks to clean up...")
    tasks = asyncio.all_tasks(loop=loop)
    print(f"Gracefully cleaning up {len(tasks)} tasks")
    for task in tasks:
        task.cancel()
        with suppress(asyncio.CancelledError):
            loop.run_until_complete(task)

    print("Closing loop...")
    loop.close()
