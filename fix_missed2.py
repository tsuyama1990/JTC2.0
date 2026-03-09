from pathlib import Path

rag_path = Path("src/data/rag.py")
content = rag_path.read_text()

# Reduce statements in `_scan_dir_size`
match = """        try:
            real_path = os.path.realpath(current_path)
            if real_path in visited_realpaths:
                continue
            visited_realpaths.add(real_path)

            with os.scandir(current_path) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue

                        if entry.is_file(follow_symlinks=False):
                            try:
                                stat_res = entry.stat(follow_symlinks=False)
                                total_size += stat_res.st_size
                                file_count += 1
                            except OSError as e:
                                logger.warning(f"Error stating file {entry.path}: {e}")
                                continue

                            if file_count > max_files:
                                logger.warning(f"Scan file limit reached.")
                                return total_size
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append((entry.path, current_depth + 1))
                    except PermissionError:
                        logger.warning(f"Permission denied accessing entry: {entry.name}")
                    except OSError as e:
                        logger.warning(f"OS error accessing entry: {entry.name}, {e}")

        except PermissionError:
            logger.warning(f"Permission denied accessing directory: {current_path}")
        except OSError as e:
            logger.warning(f"OS error accessing directory: {current_path}, {e}")"""

replacement = """        try:
            real_path = os.path.realpath(current_path)
            if real_path in visited_realpaths:
                continue
            visited_realpaths.add(real_path)

            with os.scandir(current_path) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_file(follow_symlinks=False):
                            try:
                                total_size += entry.stat(follow_symlinks=False).st_size
                                file_count += 1
                            except OSError:
                                continue
                            if file_count > max_files:
                                return total_size
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append((entry.path, current_depth + 1))
                    except OSError:
                        pass
        except OSError:
            pass"""

content = content.replace(match, replacement)
rag_path.write_text(content)
