def format_number(n, decimals=2):
    if n is None or n == "":
        return ""
    try:
        return f"{float(n):,.{decimals}f}"
    except (ValueError, TypeError):
        return str(n)


def wrap_text(canvas_obj, text, font_name, font_size, max_width):
    if not text:
        return [""]
    words = str(text).split()
    if not words:
        return [""]

    space_width = canvas_obj.stringWidth(" ", font_name, font_size)
    lines = []
    current_line = []
    current_width = 0

    for word in words:
        word_width = canvas_obj.stringWidth(word, font_name, font_size)
        
        if current_line and (current_width + word_width <= max_width):
            current_line.append(word)
            current_width += word_width + space_width
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width + space_width

    if current_line:
        lines.append(" ".join(current_line))
    return lines or [""]