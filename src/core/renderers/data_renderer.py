from typing import Any


class DataRenderer:
    """Renderer for converting data dictionaries into formatted strings."""

    def __init__(self, indent_size: int = 2, list_bullet: str = "-", max_depth: int = 50, output_format: str = "text") -> None:
        self.indent_size = indent_size
        self.list_bullet = list_bullet
        self.max_depth = max_depth
        self.output_format = output_format

    def render_to_strings(self, data: dict[str, Any]) -> list[str]:
        """Convert a dictionary into a list of formatted strings using an iterative approach."""
        if self.output_format == "json":
            import json
            return json.dumps(data, indent=self.indent_size).split("\n")

        result = []
        # Stack items: (item, indent_level, key_for_dict_item)
        stack: list[tuple[Any, int, str | None]] = [(data, 0, None)]

        while stack:
            current_item, indent_level, current_key = stack.pop()

            if indent_level > self.max_depth:
                msg = f"DataRenderer exceeded maximum recursion depth of {self.max_depth}"
                raise ValueError(msg)

            indent_str = (" " * self.indent_size) * indent_level

            if isinstance(current_item, dict):
                if current_key is not None:
                    title_key = current_key.replace("_", " ").title()
                    result.append(f"{indent_str}{title_key}:")
                    indent_level += 1

                # To maintain original output order, process items in reverse
                for k, v in reversed(list(current_item.items())):
                    stack.append((v, indent_level, k))

            elif isinstance(current_item, list):
                if current_key is not None:
                    title_key = current_key.replace("_", " ").title()
                    result.append(f"{indent_str}{title_key}:")
                    indent_level += 1

                for v in reversed(current_item):
                    # We pass None for key to indicate it's a list item
                    stack.append((v, indent_level, None))
            elif current_key is not None:
                title_key = current_key.replace("_", " ").title()
                result.append(f"{indent_str}{title_key}: {current_item!s}")
            else:
                # List item
                list_indent = (" " * self.indent_size) * max(0, indent_level - 1)
                result.append(f"{list_indent} {self.list_bullet} {current_item!s}")

        return result
