from typing import Any


class DataRenderer:
    """Renderer for converting data dictionaries into formatted strings."""

    @staticmethod
    def render_to_strings(data: dict[str, Any], max_depth: int = 50) -> list[str]:
        """Convert a dictionary into a list of formatted strings using an iterative approach."""
        result = []
        # Stack items: (item, indent, key_for_dict_item)
        stack: list[tuple[Any, int, str | None]] = [(data, 0, None)]

        while stack:
            current_item, indent, current_key = stack.pop()

            if indent > max_depth:
                msg = f"DataRenderer exceeded maximum recursion depth of {max_depth}"
                raise ValueError(msg)

            indent_str = "  " * indent

            if isinstance(current_item, dict):
                if current_key is not None:
                    title_key = current_key.replace("_", " ").title()
                    result.append(f"{indent_str}{title_key}:")
                    indent += 1

                # To maintain original output order, process items in reverse
                for k, v in reversed(list(current_item.items())):
                    stack.append((v, indent, k))

            elif isinstance(current_item, list):
                if current_key is not None:
                    title_key = current_key.replace("_", " ").title()
                    result.append(f"{indent_str}{title_key}:")
                    indent += 1

                for v in reversed(current_item):
                    # We pass None for key to indicate it's a list item
                    stack.append((v, indent, None))
            elif current_key is not None:
                title_key = current_key.replace("_", " ").title()
                result.append(f"{indent_str}{title_key}: {current_item!s}")
            else:
                # List item
                result.append(f"{'  ' * (indent - 1)}  - {current_item!s}")

        return result
