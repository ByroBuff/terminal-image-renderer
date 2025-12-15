import os
import sys
from PIL import Image
import argparse
import time

UPPER_HALF = "▀"
LOWER_HALF = "▄"
FULL_BLOCK = "█"

RESET_ALL = "\x1b[0m"
RESET_BG = "\x1b[49m"
RESET_FG = "\x1b[39m"

def ansi_fg(r, g, b):
    return f"\x1b[38;2;{r};{g};{b}m"

def ansi_bg(r, g, b):
    return f"\x1b[48;2;{r};{g};{b}m"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def reset_buffer():
    for r in range(height):
        row = _cells[r]
        for c in range(width):
            row[c]["upper"] = None
            row[c]["lower"] = None
            
def resize_buffers(new_width, new_height):
    """Resize global width/height and reinitialize buffers."""
    global width, height, _cells
    width, height = new_width, new_height
    _cells = [[{"upper": None, "lower": None} for _ in range(width)] for _ in range(height)]

def is_valid_position(row, col):
    return 1 <= row <= height and 1 <= col <= width


width, height = os.get_terminal_size()
# in-memory screen buffer
_cells = [[{"upper": None, "lower": None} for _ in range(width)] for _ in range(height)]

def move_cursor_to(row, col):
    """
    Moves the terminal cursor to a specific row and column using ANSI codes.
    """
    print(f"\x1b[{row};{col}H", end="")
    sys.stdout.flush()
    
# unused
def draw_cell(row, col):
    """
    Render a single terminal cell based on its upper/lower colors.
    """
    if not is_valid_position(row, col):
        return
    
    cell = _cells[row - 1][col - 1]
    upper = cell["upper"]
    lower = cell["lower"]

    move_cursor_to(row, col)

    if upper is None and lower is None:
        
        sys.stdout.write(RESET_ALL + " " + RESET_ALL)
        sys.stdout.flush()
        return

    if upper is not None and lower is not None:
        
        if upper == lower:
            r, g, b = upper
            sys.stdout.write(ansi_fg(r, g, b) + FULL_BLOCK + RESET_ALL)
            sys.stdout.flush()
            return
        
        ur, ug, ub = upper
        lr, lg, lb = lower
        sys.stdout.write(ansi_fg(ur, ug, ub) + ansi_bg(lr, lg, lb) + UPPER_HALF + RESET_ALL)
        sys.stdout.flush()
        return

    if upper is not None:
        r, g, b = upper
        sys.stdout.write(ansi_fg(r, g, b) + RESET_BG + UPPER_HALF + RESET_ALL)
        sys.stdout.flush()
        return

    r, g, b = lower
    sys.stdout.write(ansi_fg(r, g, b) + RESET_BG + LOWER_HALF + RESET_ALL)
    sys.stdout.flush()

def set_pixel(x, y, r, g, b):
    """
    Update the in-memory buffer with the color of a pixel at (x, y).
    """
    row = (y // 2) + 1
    col = x + 1
    
    if not is_valid_position(row, col):
        return

    cell = _cells[row - 1][col - 1]
    if y % 2 == 0:
        cell["upper"] = (r, g, b)
    else:
        cell["lower"] = (r, g, b)

    return

def compose_cell(cell):
    """
    Returns the character, foreground and background colors for a cell
    """
    upper = cell["upper"]
    lower = cell["lower"]
    
    if upper is None and lower is None:
        return " ", None, None
    
    if upper is not None and lower is not None:
        if upper == lower:
            return FULL_BLOCK, upper, None
        
        return UPPER_HALF, upper, lower
    
    if upper is not None:
        return UPPER_HALF, upper, None
    
    return LOWER_HALF, lower, None

def draw_row(row):
    if not (1 <= row <= height):
        return
    
    move_cursor_to(row, 1)
    parts = []
    cur_fg = None
    cur_bg = None
    for col in range(1, width + 1):
        ch, fg, bg = compose_cell(_cells[row - 1][col - 1])
        seq = []
        if fg != cur_fg:
            if fg is None:
                seq.append(RESET_FG)
            else:
                r, g, b = fg
                seq.append(ansi_fg(r, g, b))
            cur_fg = fg
        if bg != cur_bg:
            if bg is None:
                seq.append(RESET_BG)
            else:
                r, g, b = bg
                seq.append(ansi_bg(r, g, b))
            cur_bg = bg
        seq.append(ch)
        parts.append("".join(seq))
    parts.append(RESET_ALL)
    sys.stdout.write("".join(parts))
    sys.stdout.flush()

def render_image(img_path, scale=1.0):
    img = Image.open(img_path).convert("RGB")
    img_w, img_h = img.size

    max_w = width
    max_h = height * 2

    # Preserve aspect ratio for rendering to terminal sizes different from the image
    scale = min(max_w / img_w, max_h / img_h) * scale
    new_w = max(1, min(max_w, int(img_w * scale)))
    new_h = max(1, min(max_h, int(img_h * scale)))
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Center the image within the terminal area
    x_off = (max_w - new_w) // 2
    y_off = (max_h - new_h) // 2

    clear_screen()
    reset_buffer()
    pixels = img.load()
    for y in range(new_h):
        for x in range(new_w):
            r, g, b = pixels[x, y]
            set_pixel(x + x_off, y + y_off, r, g, b)

    for r in range(1, height + 1):
        draw_row(r)
        
    move_cursor_to(height, 1)
    sys.stdout.write(RESET_ALL)
    sys.stdout.flush()

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Render an image in the terminal")
    parser.add_argument("image_path", help="Path to the image file to render")
    parser.add_argument("--watch", "-w", action="store_true", help="Watch for terminal resize and update the render")
    parser.add_argument("--scale", "-s", type=float, default=1.0, help="Scaling factor for the image")
    args = parser.parse_args()

    render_image(args.image_path, args.scale)
    
    if args.watch:
        try:
            last_size = os.get_terminal_size()
            while True:
                cur_size = os.get_terminal_size()
                if (cur_size.columns != last_size.columns) or (cur_size.lines != last_size.lines):
                    resize_buffers(cur_size.columns, cur_size.lines)
                    render_image(args.image_path, args.scale)
                    last_size = cur_size
                    
                time.sleep(0.1)
        except KeyboardInterrupt:
            move_cursor_to(height, 1)
            sys.stdout.write(RESET_ALL)
            sys.stdout.flush()