# Recetas/main/templatetags/ui_extras.py
from django import template

register = template.Library()

def _hex_to_rgb(hex_color: str):
    hex_color = (hex_color or "").lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c*2 for c in hex_color])
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return r, g, b
    except Exception:
        return 230, 230, 230

@register.filter
def contrast_color(hex_color: str):
    """Devuelve '#000' o '#fff' según luminancia del fondo."""
    r, g, b = _hex_to_rgb(hex_color)
    y = (0.2126*(r/255)**2.2 + 0.7152*(g/255)**2.2 + 0.0722*(b/255)**2.2)
    return "#000" if y > 0.5 else "#fff"
