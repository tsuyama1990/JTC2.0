from typing import Any


class DataRenderer:
    """Extracts rendering logic for data structures (used primarily for PDF generation)."""

    @staticmethod
    def render_dict(data: dict[str, Any]) -> list[str]:
        """Convert dictionary to a formatted list of strings."""
        lines: list[str] = []

        def traverse_list(lst: list[Any], indent: int) -> None:
            for item in lst:
                if isinstance(item, dict):
                    traverse_dict(item, indent)
                else:
                    lines.append(f"{'  ' * (indent - 1)}  - {item!s}")

        def traverse_dict(d: dict[str, Any], indent: int = 0) -> None:
            for key, value in d.items():
                indent_str = "  " * indent
                title_key = key.replace("_", " ").title()

                if isinstance(value, dict):
                    lines.append(f"{indent_str}{title_key}:")
                    traverse_dict(value, indent + 1)
                elif isinstance(value, list):
                    lines.append(f"{indent_str}{title_key}:")
                    traverse_list(value, indent + 1)
                else:
                    lines.append(f"{indent_str}{title_key}: {value!s}")

        traverse_dict(data)
        return lines
