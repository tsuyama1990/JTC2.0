from pathlib import Path

rag_path = Path("src/data/rag.py")
content = rag_path.read_text()
# Remove duplicated depth limits
match = """    if depth_limit is not None and depth_limit > 100:
        msg = "depth_limit exceeds safety bounds"
        raise ValueError(msg)

    if depth_limit is not None and depth_limit > 100:
        msg = "depth_limit exceeds safety bounds"
        raise ValueError(msg)"""

replacement = """    if depth_limit is not None and depth_limit > 100:
        msg = "depth_limit exceeds safety bounds"
        raise ValueError(msg)"""

content = content.replace(match, replacement)
rag_path.write_text(content)
