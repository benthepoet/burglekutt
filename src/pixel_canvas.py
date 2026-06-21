"""Fast Tk canvas rendering for resolved pixel grids via PhotoImage."""

import tkinter as tk


def hex_color_to_rgb(hex_color):
    """Convert #RRGGBB to an (r, g, b) tuple."""
    value = hex_color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def ppm_bytes_from_pixels(pixels, scale=1):
    """Build raw PPM bytes for a 2D grid of #RRGGBB colors."""
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    out_width = width * scale
    out_height = height * scale
    header = "P6\n{} {}\n255\n".format(out_width, out_height).encode("ascii")
    body = bytearray()
    for row in range(height):
        for _repeat_row in range(scale):
            for col in range(width):
                rgb = hex_color_to_rgb(pixels[row][col])
                for _repeat_col in range(scale):
                    body.extend(rgb)
    return header + bytes(body)


def photoimage_from_pixels(pixels, scale=1):
    """Return a PhotoImage scaled with nearest-neighbor sampling."""
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    if width == 0 or height == 0:
        return tk.PhotoImage(width=1, height=1)
    ppm = ppm_bytes_from_pixels(pixels, scale)
    out_width = width * scale
    out_height = height * scale
    return tk.PhotoImage(width=out_width, height=out_height, data=ppm, format="PPM")


def draw_pixel_grid(canvas, pixels, scale=1):
    """Replace canvas contents with one PhotoImage for the pixel grid."""
    photo = photoimage_from_pixels(pixels, scale)
    canvas.delete("all")
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas._pixel_photo = photo