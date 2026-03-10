from typing import Any




class DataRenderer:
    """Renderer for converting data dictionaries into formatted strings."""

    @staticmethod
    def render_to_strings(data: dict[str, Any]) -> list[str]:
        """Convert a dictionary into a list of formatted strings."""
        result = []
        settings = get_settings().render

        indent_char = " " * settings.indent_spaces

        def add_list_to_strings(lst: list[Any], indent: int) -> None:
            if indent > settings.max_depth:
                return
            for item in lst:
                if isinstance(item, dict):
                    add_dict_to_strings(item, indent)
                else:
                    prefix_indent = indent_char * (indent - 1) if indent > 0 else ""
                    result.append(f"{prefix_indent}  - {item!s}")

        def add_dict_to_strings(d: dict[str, Any], indent: int = 0) -> None:
            if indent > settings.max_depth:
                return
            for key, value in d.items():
                indent_str = indent_char * indent
                title_key = key.replace("_", " ").title()

                if isinstance(value, dict):
                    result.append(f"{indent_str}{title_key}:")
                    add_dict_to_strings(value, indent + 1)
                elif isinstance(value, list):
                    result.append(f"{indent_str}{title_key}:")
                    add_list_to_strings(value, indent + 1)
                else:
                    result.append(f"{indent_str}{title_key}: {value!s}")

        add_dict_to_strings(data)
        return result
