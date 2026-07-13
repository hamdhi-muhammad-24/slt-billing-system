from core.text_utils import wrap_text, format_number


def draw_table_with_overflow(renderer, config, data):
    if not data:
        return []

    y = config["y_start"]
    y_min = config["y_min"]
    line_h = config["line_h"]
    font_size = config["font_size"]

    overflow = []

    for idx, row in enumerate(data):
        # Precompute wrapped lines for this row
        row_lines = {}
        for col in config["columns"]:
            value = row.get(col["field"], "")
            if col.get("format") == "number":
                value = format_number(value, col.get("decimals", 2))

            if col.get("wrap") and "max_x" in col:
                max_width = col["max_x"] - col["x"]
                lines = wrap_text(renderer.canvas, str(value),
                                   renderer.FONT_NAME, font_size, max_width)
            else:
                lines = [str(value) if value else ""]
            row_lines[col["field"]] = lines

        # Row height = max lines in any column × line_h
        row_height = max(len(lines) for lines in row_lines.values()) * line_h

        # Check if fits on current page
        if y - row_height < y_min:
            overflow = data[idx:]
            break

        # Draw row
        first_line_y = y
        for col in config["columns"]:
            lines = row_lines[col["field"]]
            hanging_indent = col.get("hanging_indent", 0)
            col_y = first_line_y

            for i, line in enumerate(lines):
                x = col["x"] if i == 0 else col["x"] + hanging_indent
                renderer.text(x, col_y, line,
                              size=font_size,
                              bold=col.get("bold", False),
                              align=col.get("align", "left"))
                col_y -= line_h

        y -= row_height

    return overflow