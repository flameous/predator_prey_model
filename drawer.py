import tkinter
import time
import json

import main_logic


def hex_color(red: int, green: int, blue: int) -> str:
    color = '#'
    for num in [red, green, blue]:
        if num > 255:
            num = 255

        hex_str = str(hex(num))[2:]
        color += '0' * (2 - len(hex_str)) + hex_str

    return color


color_predator = hex_color(100, 150, 100)
color_prey = hex_color(32, 75, 100)

root = tkinter.Tk()
c = tkinter.Canvas(root, height=600, width=600)

t = time.time()
tick = 0
with open('data.log', 'r') as f:
    world_size = int(f.readline())
    ratio = 600 // world_size

    for line in f.readlines():
        tick += 1

        predators = 0
        preys = 0

        c.create_rectangle(0, 0, 700, 700, fill='white')
        while time.time() - t < 0.2:
            pass

        t = time.time()

        data = json.loads(line)
        for animal in data:
            x1 = ratio * animal['x']
            y1 = ratio * animal['y']
            x2 = ratio * (animal['x'] + 1)
            y2 = ratio * (animal['y'] + 1)

            if animal['type'] == 'predator':
                fill_color = hex_color(255 * animal['life'] // 100, 0, 0)
                predators += 1
            else:
                fill_color = hex_color(0, 255 * animal['life'] // 100, 0)
                preys += 1

            c.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline=fill_color)
            c.pack()

        c.create_text(300, 20,
                      fill='red',
                      text='predators (red): %d. preys (green): %d. tick: %d' % (predators, preys, tick))
        root.update()
