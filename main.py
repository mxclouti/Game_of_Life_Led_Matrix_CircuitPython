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

# https://github.com/adafruit/Adafruit_CircuitPython_Display_Text/tree/main/adafruit_display_text
# https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font/tree/main/adafruit_bitmap_font

import board
import displayio
import framebufferio
import rgbmatrix
import busio
import board
import gc

# from digitalio import DigitalInOut, Direction
import adafruit_display_text.label

import terminalio
from adafruit_bitmap_font import bitmap_font
import time

# from math import sin
# import math
import random
import array

BOARD_SIZE = 64
SQUARE_SIZE = 1
GRID_SIZE = BOARD_SIZE // SQUARE_SIZE
NUM_CELLS = GRID_SIZE * GRID_SIZE
MAX_GENERATIONS = 600
BIT_DEPTH_VALUE = 4
SERPENTINE_VALUE = True
DISPLAY_TEXT = True
ROTATION = 0

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=BOARD_SIZE,
    height=BOARD_SIZE,
    bit_depth=BIT_DEPTH_VALUE,
    rgb_pins=[board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5],
    addr_pins=[board.GP6, board.GP7, board.GP8, board.GP9, board.GP10],
    clock_pin=board.GP11,
    latch_pin=board.GP12,
    output_enable_pin=board.GP13,
    tile=1,
    serpentine=SERPENTINE_VALUE,
    doublebuffer=True,
)

DISPLAY = framebufferio.FramebufferDisplay(matrix, auto_refresh=True, rotation=ROTATION)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

#REGISTERS = (0, 256)  # Range of registers to read, from the first up to (but
                      # not including!) the second value.

#REGISTER_SIZE = 2     # Number of bytes to read from each register.

class RGB_Api:
    def __init__(self):
        self.bitmapGOL = displayio.Bitmap(64, 64, 5)
        self.i2c1DS1307 = busio.I2C(scl=board.GP19, sda=board.GP18, frequency=400000)

    """
    def scanI2CDevices(self):
        while not self.i2c1DS1307.try_lock():
            pass
        # Find the first I2C device available.
        devices = self.i2c1DS1307.scan()
        while len(devices) < 1:
            devices = self.i2c1DS1307.scan()
        device = devices[0]
        print('Found device with address: {}'.format(hex(device)))
        # Scan all the registers and read their byte values.
        result = bytearray(REGISTER_SIZE)
        for register in range(*REGISTERS):
            try:
                i2c1DS1307.writeto(device, bytes([register]))
                i2c1DS1307.readfrom_into(device, result)
            except OSError:
                continue  # Ignore registers that don't exist!
            print('Address {0}: {1}'.format(hex(register), ' '.join([hex(x) for x in result])))

        # Unlock the I2C bus when finished.  Ideally put this in a try-finally!
        i2c1DS1307.unlock()
    """

    def decimal_to_bcd(self, decimal):
        """Convert decimal to BCD."""
        return (decimal // 10) << 4 | (decimal % 10)

    def setDs1307Time(self, year, month, date, day, hours, minutes, seconds):

        # Convert decimal values to BCD
        seconds_bcd = self.decimal_to_bcd(seconds)
        minutes_bcd = self.decimal_to_bcd(minutes)
        hours_bcd = self.decimal_to_bcd(hours)
        day_bcd = self.decimal_to_bcd(day)
        date_bcd = self.decimal_to_bcd(date)
        month_bcd = self.decimal_to_bcd(month)
        year_bcd = self.decimal_to_bcd(year % 100)

        # Ensure the clock is not halted (clear CH bit in seconds register)
        seconds_bcd &= 0x7F  # Clear bit 7 (CH bit)

        # Prepare data to write (register 0x00 to 0x06)
        data = bytearray([
            0x00,  # Start at register 0x00 (seconds)
            seconds_bcd,
            minutes_bcd,
            hours_bcd,
            day_bcd,
            date_bcd,
            month_bcd,
            year_bcd,
        ])

        while not self.i2c1DS1307.try_lock():
            pass

        try:
            self.i2c1DS1307.writeto(0x68, data)
        finally:
            self.i2c1DS1307.unlock()

    def readDs1307Time(self):
        while not self.i2c1DS1307.try_lock():
            pass

        try:
            # Read 7 bytes from register 0x00 (seconds, minutes, hours, day, date, month, year)
            # BCD (Binary-Coded Decimal) format
            self.i2c1DS1307.writeto(0x68, bytearray([0x00]))
            data = bytearray(7)
            self.i2c1DS1307.readfrom_into(0x68, data)
        finally:
            self.i2c1DS1307.unlock()

        # Convert BCD to decimal
        seconds = (data[0] & 0x0F) + ((data[0] >> 4) & 0x07) * 10
        minutes = (data[1] & 0x0F) + ((data[1] >> 4) & 0x07) * 10
        hours = (data[2] & 0x0F) + ((data[2] >> 4) & 0x03) * 10
        day = data[3] & 0x07
        date = (data[4] & 0x0F) + ((data[4] >> 4) & 0x03) * 10
        month = (data[5] & 0x0F) + ((data[5] >> 4) & 0x01) * 10
        year = (data[6] & 0x0F) + ((data[6] >> 4) & 0x0F) * 10 + 2000

        return (f"{year}", f"{month}", f"{date}", f"{day}", f"{hours}", f"{minutes}", f"{seconds}")

    def getWeekday(self):
        data = i2c1DS1307.readfrom_mem(0x68, 0x00, 7)
        return WEEKDAYS[(data[3] & 0x07) - 1]

    def getDateTime(self):
        ds1370Time = self.readDs1307Time()
        return f"{ds1370Time[0]}/{ds1370Time[1]:0>2}/{ds1370Time[2]:0>2}  {ds1370Time[4]:0>2}:{ds1370Time[5]:0>2}"

    def getDate(self):
        ds1370Time = self.readDs1307Time()
        return f"{ds1370Time[0]}/{ds1370Time[1]:0>2}/{ds1370Time[2]:0>2}"

    def getTime(self):
        ds1370Time = self.readDs1307Time()
        return f"{ds1370Time[4]:0>2}:{ds1370Time[5]:0>2}:{ds1370Time[6]:0>2}"

    def drawSquare(self, x, y, color):
        pos_x = x * SQUARE_SIZE
        pos_y = y * SQUARE_SIZE
        for x in range(pos_x, pos_x + SQUARE_SIZE, 1):
            for y in range(pos_y, pos_y + SQUARE_SIZE, 1):
                self.bitmapGOL[x, y] = color

    def displayTime(self, text):
        time = self.getTime()
        text.text = time
        (text_width, text_height) = text.bounding_box[2:4]  # Width and height of the text
        #baseline = text.baseline
        text.x = (BOARD_SIZE - text_width) // 2
        text.y = (BOARD_SIZE // 2) - (text_height // 2) + 6 #+ baseline // 2

    def displayDate(self, text):
        date = self.getDate()
        text.text = date
        (text_width, text_height) = text.bounding_box[2:4]  # Width and height of the text
        #baseline = text.baseline
        text.x = (BOARD_SIZE - text_width) // 2
        text.y = (BOARD_SIZE // 2) - (text_height // 2) + 6 #+ baseline // 2

    def fillGrid(self, grid):
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                grid[y * GRID_SIZE + x] = random.randint(0, 1)

    def gameOfLife(self):
        font = bitmap_font.load_font("lib/fonts/helvR08.bdf")

        text = adafruit_display_text.label.Label(
            terminalio.FONT,
            color=0x666600,
            background_color=0x000000,
            scale=1,
            background_tight=False,
            text="",
            line_spacing=0.8,
        )

        text.x = 0
        text.y = 59
        text.hidden = not DISPLAY_TEXT

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

        DIRECTIONS = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

        all_neighbors_positions = array.array(
            "i", [0] * (GRID_SIZE * GRID_SIZE * 8)
        )  # 32768

        #self.scanI2CDevices()

        print(
            f"calculating neighbors positions 64x64x8 = {len(all_neighbors_positions)} ... "
        )

        index = 0
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                for dx, dy in DIRECTIONS:
                    nx = (x + dx) % GRID_SIZE
                    ny = (y + dy) % GRID_SIZE
                    all_neighbors_positions[index] = ny * GRID_SIZE + nx
                    index += 1

        grid = array.array("B", [0] * (GRID_SIZE * GRID_SIZE))
        new_grid = array.array("B", [0] * (GRID_SIZE * GRID_SIZE))

        grid_view = memoryview(grid)
        new_grid_view = memoryview(new_grid)

        y_indices = array.array("I", [0] * GRID_SIZE)
        for y in range(GRID_SIZE):
            y_indices[y] = y * GRID_SIZE

        print("filling grid with random cells ...")

        self.fillGrid(grid)

        generation = 0

        print("starting simulation ...")

        #self.setDs1307Time(2025, 2, 6, 4, 8, 23, 0)

        if DISPLAY_TEXT:
            self.displayTime(text)

        start_time = time.monotonic()

        displayWhat = 0

        while True:

            alive = 0

            for index in range(NUM_CELLS):
                live_neighbors = 0
                for indexNeighbor in range(index * 8, (index * 8) + 8, 1):
                    live_neighbors += grid[all_neighbors_positions[indexNeighbor]]
                if grid[index] == 1:  # alive
                    # stay alive if 2 or 3 neighbors
                    new_grid[index] = 1 if live_neighbors in [2, 3] else 0
                else:  # dead
                    # relive if 3 neighbors
                    new_grid[index] = 1 if live_neighbors == 3 else 0
                alive += new_grid[index]

            grid_view[:] = new_grid_view[:]

            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    if SQUARE_SIZE == 1:
                        self.bitmapGOL[x, y] = grid[y_indices[y] + x]
                    else:
                        self.drawSquare(x, y, grid[y_indices[y] + x])

            #if DISPLAY_TEXT:
            #    text.text = f"{generation}-{alive}"

            if DISPLAY_TEXT:
                elapsed = time.monotonic() - start_time
                if elapsed > 1:
                    if displayWhat == 0:
                        self.displayTime(text)
                    else:
                        self.displayDate(text)
                if elapsed > 4:
                    start_time = time.monotonic()
                    displayWhat = not displayWhat

            generation += 1

            if generation == MAX_GENERATIONS:
                generation = 0
                palette[1] = random.randint(1, 262142)
                self.fillGrid(grid)

            DISPLAY.refresh()

if __name__ == "__main__":
    #gc.collect()
    RGB = RGB_Api()
    while True:
        RGB.gameOfLife()

"""
byte customChar0[] = {
  0x07,
  0x07,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18
};

byte customChar1[] = {
  0x1F,
  0x1F,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00
};

byte customChar2[] = {
  0x1C,
  0x1C,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03
};

byte customChar3[] = {
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x00
};


byte customChar4[] = {
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x00
};

byte customChar5[] = {
  0x00,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18
};

byte customChar6[] = {
  0x00,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03
};


byte customChar7[] = {
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x07,
  0x07
};

byte customChar8[] = {
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x1F,
  0x1F
};

byte customChar9[] = {
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x1C,
  0x1C
};

byte customChar10[] = {
  0x07,
  0x07,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00
};

byte customChar11[] = {
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x07
};

byte customChar12[] = {
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x1F
};

byte customChar13[] = {
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x1C
};

byte customChar14[] = {
  0x07,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18
};

byte customChar15[] = {
  0x1F,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00
};

byte customChar16[] = {
  0x1C,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00
};

byte customChar17[] = {
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x1C,
  0x1C
};

byte customChar18[] = {
  0x07,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00
};

byte customChar19[] = {
  0x1C,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03
};

byte customChar20[] = {
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x07,
  0x07
};

byte customChar21[] = {
  0x00,
  0x00,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18
};

byte customChar22[] = {
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x18,
  0x07
};

byte customChar23[] = {
  0x1C,
  0x1C,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00
};

byte customChar24[] = {
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x00,
  0x1C
};

byte customChar25[] = {
  0x00,
  0x00,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03
};

byte customChar26[] = {
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x03,
  0x00,
  0x00
};




"""
