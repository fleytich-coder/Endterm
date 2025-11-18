import asyncio
import logging
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Tuple

from .decorators import log_call, measure_time_sync
from .exceptions import InvalidLogFormatError
from .parser import iter_log_lines, generate_parsed_entries, follow_log, parse_log_line

logger = logging.getLogger(__name__)


class LogAnalyzer:


    def __init__(self) -> None:
        self._counter = Counter()

    @log_call
    def consume(self, level: str, message: str) -> None:
        """Добавляет одну запись в статистику."""
        self._counter[level] += 1

    def snapshot(self) -> Dict[str, int]:
        """Возвращает текущее состояние счётчика как обычный dict."""
        return dict(self._counter)


@measure_time_sync
def analyze_file_sync(path: str | Path) -> Dict[str, int]:

    analyzer = LogAnalyzer()
    lines = iter_log_lines(path)
    for level, message in generate_parsed_entries(lines):
        analyzer.consume(level, message)

    return analyzer.snapshot()


def _parse_line_safe(line: str) -> Tuple[str | None, str | None]:

    try:
        parsed = parse_log_line(line)
        return parsed["level"], parsed["message"]
    except InvalidLogFormatError:
        return None, None


@measure_time_sync
def analyze_file_threaded(
    path: str | Path,
    workers: int = 4,
) -> Dict[str, int]:

    analyzer = LogAnalyzer()
    lines = list(iter_log_lines(path))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for level, message in executor.map(_parse_line_safe, lines):
            if level is None:
                continue
            analyzer.consume(level, message)

    return analyzer.snapshot()


async def analyze_file_async_streaming(
    path: str | Path,
    runtime_seconds: int = 15,
    stats_interval: int = 5,
) -> Tuple[Dict[str, int], float]:
   
    analyzer = LogAnalyzer()
    stop_event = asyncio.Event()
    start_time = asyncio.get_running_loop().time()

    async def reader_task() -> None:
        async for raw_line in follow_log(path):
            if stop_event.is_set():
                break
            try:
                parsed = parse_log_line(raw_line)
            except InvalidLogFormatError:
                continue
            analyzer.consume(parsed["level"], parsed["message"])

    async def reporter_task() -> None:
        while not stop_event.is_set():
            await asyncio.sleep(stats_interval)
            snapshot = analyzer.snapshot()
            logger.info("[ASYNC STATS] %s", snapshot)
            print(f"[ASYNC STATS] {snapshot}")

    # Запускаем параллельно чтение и периодическую печать статистики
    reader = asyncio.create_task(reader_task())
    reporter = asyncio.create_task(reporter_task())

    try:
        # Ограничиваем общее время работы
        await asyncio.sleep(runtime_seconds)
    finally:
        stop_event.set()
        await asyncio.gather(reader, reporter, return_exceptions=True)

    elapsed = asyncio.get_running_loop().time() - start_time
    return analyzer.snapshot(), elapsed
