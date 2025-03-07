import threading
import sys
import os
import shutil
from typing import Tuple


class ThreadSafeCounter:
    def __init__(self) -> None:
        self._count = 0
        self._lock = threading.Lock()

    def increment_and_get(self) -> int:
        with self._lock:
            self._count += 1
            return self._count

    def reset(self) -> None:
        with self._lock:
            self._count = 0


def display_progress_bar(max_value: int, file_counter: ThreadSafeCounter) -> None:
    bar_length = 50
    current_value = file_counter.increment_and_get()
    progress = current_value / max_value
    block = int(round(bar_length * progress))
    text = f"\rProgress: [{'#' * block + '-' * (bar_length - block)}] {current_value}/{max_value}"
    sys.stdout.write(text)
    sys.stdout.flush()


def split_integer_into_intervals(integer: int, n: int) -> list[Tuple[int, int]]:
    interval_size = integer // n
    remainder = integer % n
    intervals = [(i * interval_size, (i + 1) * interval_size) for i in range(n)]
    if remainder:
        intervals[-1] = (intervals[-1][0], intervals[-1][1] + remainder)
    return intervals


def find_last_non_empty_line(text: str) -> str:
    lines = text.splitlines()
    for line in reversed(lines):
        if line.strip():
            return line
    raise Exception("Failed to find the last non-empty line in m3u8 playlist.")


def find_closest(arr: list[int], target: int) -> int:
    closest = arr[0]
    min_diff = abs(arr[0] - target)
    for num in arr:
        diff = abs(num - target)
        if diff < min_diff:
            min_diff = diff
            closest = num
    return closest


def delete_all_subfolders(folder_path: str) -> None:
    if not os.path.exists(folder_path):
        return
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
