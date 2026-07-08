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

    lines = []
    current = ""

    for word in words:
        if canvas_obj.stringWidth(word, font_name, font_size) > max_width:
            if current:
                lines.append(current)
                current = ""
            chunk = ""
            for ch in word:
                test = chunk + ch
                if canvas_obj.stringWidth(test, font_name, font_size) <= max_width:
                    chunk = test
                else:
                    if chunk:
                        lines.append(chunk)
                    chunk = ch
            if chunk:
                current = chunk
        else:
            test = (current + " " + word).strip()
            if canvas_obj.stringWidth(test, font_name, font_size) <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

    if current:
        lines.append(current)
    return lines or [""]