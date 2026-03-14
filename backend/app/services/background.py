from typing import Callable

from fastapi import BackgroundTasks


def schedule_task(background_tasks: BackgroundTasks | None, fn: Callable, *args, **kwargs):
    if background_tasks is None:
        return fn(*args, **kwargs)
    background_tasks.add_task(fn, *args, **kwargs)
    return None
