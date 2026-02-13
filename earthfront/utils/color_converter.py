def rgb_to_hex(rgb):
    r, g, b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")

    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
