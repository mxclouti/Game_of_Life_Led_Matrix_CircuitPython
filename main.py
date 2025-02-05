# Conway's "Game of Life"
# Martin Cloutier - February 2025
# mxclouti@gmail.com
# Led Matrix 64x64 - Hub75e
# It uses only 1 dimension arrays for speed
# and memory efficiency.
# I tried with complex data structures:
# Too slow and not enough memory.
# CircuitPython code tested on a Raspberry Pico 2 W.
# About 3 generations per second.

import board
import displayio
import framebufferio
import rgbmatrix
from digitalio import DigitalInOut,Direction
import adafruit_display_text.label
import terminalio
from adafruit_bitmap_font import bitmap_font
import time
from math import sin
import math
import random
import array

BOARD_SIZE = 64
SQUARE_SIZE = 1
GRID_SIZE = BOARD_SIZE // SQUARE_SIZE
NUM_CELLS = GRID_SIZE * GRID_SIZE

BIT_DEPTH_VALUE = 4
SERPENTINE_VALUE = True

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=BOARD_SIZE, height=BOARD_SIZE, bit_depth=BIT_DEPTH_VALUE,
    rgb_pins=[board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5],
    addr_pins=[board.GP6, board.GP7, board.GP8, board.GP9, board.GP10],
    clock_pin=board.GP11, latch_pin=board.GP12, output_enable_pin=board.GP13,
    tile=1, serpentine=SERPENTINE_VALUE,
    doublebuffer=True)

DISPLAY = framebufferio.FramebufferDisplay(matrix, auto_refresh=True, rotation=90)

class RGB_Api():

    def __init__(self):
        self.bitmapGOL = displayio.Bitmap(64, 64, 5)

    def drawSquare(self, x, y, color):
        pos_x = x * SQUARE_SIZE
        pos_y = y * SQUARE_SIZE
        for x in range(pos_x, pos_x + SQUARE_SIZE, 1):
            for y in range(pos_y, pos_y + SQUARE_SIZE, 1):
                self.bitmapGOL[x, y] = color

    def fillGrid(self, grid):
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                grid[y * GRID_SIZE + x] = random.randint(0, 1)

    def gameOfLife(self):
        font = bitmap_font.load_font("lib/fonts/helvR08.bdf")

        text = adafruit_display_text.label.Label(
            font, # terminalio.FONT,
            color=0x666600,
            scale=1,
            text='Test',
            line_spacing=0.8
            )

        text.x = 0
        text.y = 59
        text.hidden = False

        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = 0x0000FF

        main_group = displayio.Group()

        tileGrid = displayio.TileGrid(self.bitmapGOL, pixel_shader=palette)
        tileGrid.hidden = False

        main_group.append(tileGrid)
        main_group.append(text)

        DISPLAY.root_group = main_group
        DISPLAY.auto_refresh = False

        DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        all_neighbors_positions = array.array('i', [0] * (GRID_SIZE * GRID_SIZE * 8))  # 32768

        print(f"calculating neighbors positions 64x64x8 = {len(all_neighbors_positions)} ... ")

        index = 0
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                for dx, dy in DIRECTIONS:
                    nx = (x + dx) % GRID_SIZE
                    ny = (y + dy) % GRID_SIZE
                    all_neighbors_positions[index] = (ny * GRID_SIZE + nx)
                    index += 1

        grid = array.array('B', [0] * (GRID_SIZE * GRID_SIZE))
        new_grid = array.array('B', [0] * (GRID_SIZE * GRID_SIZE))

        grid_view = memoryview(grid)
        new_grid_view = memoryview(new_grid)

        y_indices = array.array('I', [0] * GRID_SIZE)
        for y in range(GRID_SIZE):
            y_indices[y] = y * GRID_SIZE

        self.fillGrid(grid)

        frame_counter = 0
        time_start = time.monotonic()

        generation = 0

        while True:

            alive = 0

            for index in range(NUM_CELLS):
                live_neighbors = 0
                for indexNeighbor in range(index * 8, (index * 8) + 8, 1):
                    live_neighbors += grid[all_neighbors_positions[indexNeighbor]]
                if grid[index] == 1:  # alive
                    new_grid[index] = 1 if live_neighbors in [2, 3] else 0  # stay alive if 2 or 3 neighbors
                else:  # dead
                    new_grid[index] = 1 if live_neighbors == 3 else 0  # relive if 3 neighbors
                alive += new_grid[index]

            grid_view[:] = new_grid_view[:]

            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    if SQUARE_SIZE == 1:
                        self.bitmapGOL[x, y] = grid[y_indices[y] + x]
                    else:
                        self.drawSquare(x, y, grid[y_indices[y] + x])

            text.text = f"{generation}-{alive}"
            generation += 1

            if generation == 1000:
                generation = 0
                self.fillGrid(grid)

            DISPLAY.refresh()

if __name__ == '__main__':
    RGB = RGB_Api()
    while True:
        RGB.gameOfLife()
