from pathlib import Path

# 1. file_service.py - implement atomic write operations
file_service_path = Path("src/core/services/file_service.py")
content = file_service_path.read_text()

match = """    def _save_text_sync(self, content: str, path: Path) -> None:
        \"\"\"Synchronous implementation of save text.\"\"\"
        import os
        import tempfile

        # Ensure parent exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write pattern: write to temp file, then atomic rename
        fd, temp_path = tempfile.mkstemp(dir=path.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            # Atomic replace
            Path(temp_path).replace(path)
            logger.info(f"File saved successfully to {path}")
        except Exception:
            import contextlib

            with contextlib.suppress(OSError):
                Path(temp_path).unlink()
            raise"""

replacement = """    def _save_text_sync(self, content: str, path: Path) -> None:
        \"\"\"Synchronous implementation of save text.\"\"\"
        import os
        import tempfile

        # Ensure parent exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write pattern: write to temp file, then atomic rename
        fd, temp_path_str = tempfile.mkstemp(dir=path.parent, text=True)
        temp_path = Path(temp_path_str)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno()) # Force write to disk

            # Verify size
            if temp_path.stat().st_size == 0 and len(content) > 0:
                raise IOError("Write failed: temp file is empty")

            # Atomic replace
            temp_path.replace(path)
            logger.info(f"File saved successfully to {path}")
        except Exception:
            import contextlib
            with contextlib.suppress(OSError):
                temp_path.unlink()
            raise"""

content = content.replace(match, replacement)
file_service_path.write_text(content)

# 2. engine.py - implement input validation for network size
engine_path = Path("src/core/nemawashi/engine.py")
content = engine_path.read_text()

match = """        n = len(network.stakeholders)
        if n == 0:
            return []"""

replacement = """        n = len(network.stakeholders)
        if n == 0:
            return []

        from src.core.config import get_settings
        settings = get_settings()
        # Protect against memory exhaustion
        if n > settings.validation.max_custom_metrics: # Reuse a safe limit
            raise ValueError(f"Network too large: {n} stakeholders.")"""

content = content.replace(match, replacement)
engine_path.write_text(content)

# 3. rag.py - add depth limit upper bound
rag_path = Path("src/data/rag.py")
content = rag_path.read_text()

match = """    if depth_limit is not None and depth_limit <= 0:
        msg = "depth_limit must be positive"
        raise ValueError(msg)"""

replacement = """    if depth_limit is not None and depth_limit <= 0:
        msg = "depth_limit must be positive"
        raise ValueError(msg)

    if depth_limit is not None and depth_limit > 100:
        msg = "depth_limit exceeds safety bounds"
        raise ValueError(msg)"""

content = content.replace(match, replacement)
rag_path.write_text(content)
