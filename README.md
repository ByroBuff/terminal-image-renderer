# Terminal Renderer

This project idea came to me when I saw an instagram post of someone using the `full block` (`█`) character to create pixel art in the terminal. I knew about the half block characters (`▀` and `▄`) and those seemed to be perfect squares which would allow for a much less elongated image and also allow for direct image rendering from a png that keeps its aspect ratio. This program works by rendering the top half and bottom half of a terminal cell with different colors using foreground and background ansi colors as well as half block characters to get any combination of 2 colors onto a single character cell.

## Installation
```
pip install -r requirements.txt
```

## Usage
```
python main.py [-h] [--watch] [--scale SCALE] image_path

positional arguments:
  image_path            Path to the image file to render

options:
  -h, --help            show this help message and exit
  --watch, -w           Watch for terminal resize and update the render
  --scale SCALE, -s SCALE
                        Scaling factor for the image
```