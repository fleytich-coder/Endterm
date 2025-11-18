import argparse
import asyncio
import logging
from pathlib import Path

from async_log_analyzer.analyzer import (
    analyze_file_sync,
    analyze_file_threaded,
    analyze_file_async_streaming,
)

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Async Log Analyzer — сравнение синхронного, многопоточного и асинхронного анализа логов."
    )
    parser.add_argument(
        "--log-file",
        type=str,
        required=True,
        help="Путь к лог-файлу (например, logs/sample.log)",
    )
    parser.add_argument(
        "--mode",
        choices=["sync", "threaded", "async"],
        default="sync",
        help="Режим работы: sync (по умолчанию), threaded, async",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Кол-во потоков для threaded режима",
    )
    parser.add_argument(
        "--runtime",
        type=int,
        default=15,
        help="Время работы async режима (секунды)",
    )
    parser.add_argument(
        "--stats-interval",
        type=int,
        default=5,
        help="Интервал печати статистики в async режиме (секунды)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    args = parse_args()

    log_path = Path(args.log_file)

    if args.mode == "sync":
        print("=== SYNC MODE ===")
        stats, elapsed = analyze_file_sync(log_path)
        print(f"Режим: синхронный")
        print(f"Статистика: {stats}")
        print(f"Время выполнения: {elapsed:.4f} сек")

    elif args.mode == "threaded":
        print("=== THREADED MODE ===")
        stats, elapsed = analyze_file_threaded(log_path, workers=args.workers)
        print(f"Режим: многопоточный (workers={args.workers})")
        print(f"Статистика: {stats}")
        print(f"Время выполнения: {elapsed:.4f} сек")

    elif args.mode == "async":
        print("=== ASYNC MODE (streaming) ===")
        # В async режиме мы читаем файл "вживую", поэтому stats будет зависеть
        # от того, сколько строк появилось за runtime секунд.
        stats, elapsed = asyncio.run(
            analyze_file_async_streaming(
                log_path,
                runtime_seconds=args.runtime,
                stats_interval=args.stats_interval,
            )
        )
        print(f"Режим: асинхронный (streaming)")
        print(f"Финальная статистика: {stats}")
        print(f"Общее время работы: {elapsed:.4f} сек")


if __name__ == "__main__":
    main()
