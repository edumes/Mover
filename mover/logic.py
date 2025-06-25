import shutil
from pathlib import Path
from typing import Callable
import time

def move_content(source_path: Path, target_path: Path, progress_callback: Callable[[float, int, int], None], status_callback: Callable[[str, bool], None]) -> None:
    target_path.mkdir(parents=True, exist_ok=True)
    items = list(source_path.iterdir())
    total = len(items)
    moved = 0
    for item in items:
        target_item = target_path / item.name
        if target_item.exists():
            continue
        try:
            shutil.move(str(item), str(target_item))
            moved += 1
            progress = (moved / total) * 100.0
            progress_callback(progress, moved, total)
        except Exception as e:
            status_callback(f"Warning: Could not move {item.name} - {str(e)}", True)
    progress_callback(100.0, moved, total)
    status_callback(f"Success! Moved {moved}/{total} items to: {target_path}", False) 