"""Shared visual primitives for GrindingStation's desktop interface."""
from PIL import Image, ImageDraw

COLORS = {
    "bg": "#0B1220", "surface": "#131F30", "surface_2": "#1B2B40",
    "border": "#2A4058", "text": "#EDF5FA", "muted": "#A5B6C9",
    "accent": "#63E6BE", "danger": "#FF8F9C",
}


def button_image(width, height, radius, top, bottom, border, glow):
    # Six pixels of transparent padding preserve the existing canvas hit areas.
    im = Image.new("RGBA", (width + 12, height + 12))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, width + 5, height + 5), radius=max(3, radius),
                        fill=bottom, outline=border, width=1)
    d.line((radius + 6, 7, width + 5 - radius, 7), fill=top, width=1)
    return im


def panel_image(width, height, radius=12, padded=False):
    pad = 6 if padded else 0
    im = Image.new("RGBA", (width + pad * 2, height + pad * 2))
    ImageDraw.Draw(im).rounded_rectangle(
        (pad, pad, width + pad - 1, height + pad - 1), radius=radius,
        fill=COLORS["surface"], outline=COLORS["border"], width=1)
    return im


BUTTON_STATES = {
    "Primary.TButton": {
        "normal": ("#63E6BE", "#185345", "#63E6BE", "#63E6BE"),
        "hover": ("#A2F5D9", "#216B58", "#A2F5D9", "#63E6BE"),
        "pressed": ("#63E6BE", "#103E35", "#63E6BE", "#63E6BE"),
        "disabled": ("#26384A", "#172233", "#26384A", "#26384A"),
    },
    "Secondary.TButton": {
        "normal": ("#2A4058", "#17263A", "#2A4058", "#2A4058"),
        "hover": ("#63E6BE", "#22374E", "#4B8F89", "#63E6BE"),
        "pressed": ("#63E6BE", "#10202D", "#63E6BE", "#63E6BE"),
        "disabled": ("#26384A", "#172233", "#26384A", "#26384A"),
    },
    "Destructive.TButton": {
        "normal": ("#FF8F9C", "#472734", "#C76D82", "#FF8F9C"),
        "hover": ("#FFB3BD", "#603044", "#FF8F9C", "#FF8F9C"),
        "pressed": ("#FF8F9C", "#361D29", "#C76D82", "#FF8F9C"),
        "disabled": ("#26384A", "#172233", "#26384A", "#26384A"),
    },
}
