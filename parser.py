import re
from typing import Generator, AsyncGenerator
import asyncio
from pathlib import Path

from .exceptions import InvalidLogFormatError, FileReadError

# Формат строки:
# [2025-11-18 12:00:01] [ERROR] Something happened
LOG_PATTERN = re.compile(
    r"^\[(?P<timestamp>.+?)\]\s+\[(?P<level>INFO|WARNING|ERROR)\]\s+(?P<message>.+)$"
)


def iter_log_lines(path: str | Path) -> Generator[str, None, None]:

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                yield line.rstrip("\n")
    except OSError as exc:
        raise FileReadError(f"Не удалось прочитать лог-файл: {path}") from exc


def parse_log_line(line: str) -> dict:

    match = LOG_PATTERN.match(line)
    if not match:
        raise InvalidLogFormatError(f"Неверный формат строки лога: {line!r}")

    return {
        "timestamp": match.group("timestamp"),
        "level": match.group("level"),
        "message": match.group("message"),
    }


def generate_parsed_entries(
    lines: Generator[str, None, None],
) -> Generator[tuple[str, str], None, None]:

    for raw_line in lines:
        try:
            parsed = parse_log_line(raw_line)
        except InvalidLogFormatError:
            # Здесь можно залогировать, но для примера просто пропустим
            continue
        yield parsed["level"], parsed["message"]


async def follow_log(
    path: str | Path,
    poll_interval: float = 0.5,
) -> AsyncGenerator[str, None]:

    try:
        with open(path, "r", encoding="utf-8") as f:
            # Переходим в конец файла, чтобы ловить только новые записи
            f.seek(0, 2)

            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(poll_interval)
                    continue
                yield line.rstrip("\n")
    except OSError as exc:
        raise FileReadError(f"Не удалось читать лог-файл: {path}") from exc
