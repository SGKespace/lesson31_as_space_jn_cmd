import asyncio
import curses
import itertools
import random
import time
from os import listdir
from os.path import isfile, join

from fire_animation import fire
from curses_tools import draw_frame, get_frame_size, read_controls
from space_garbage import fly_garbage


TIC_TIMEOUT = 0.1
ANIM_DIR = 'graphics_files'
ROCKET_FRAMES_DIR = join(ANIM_DIR, 'rocket')
GARBAGE_FRAMES_DIR = join(ANIM_DIR, 'garbage')


async def go_to_sleep(seconds):
    iteration_count = int(seconds * 10)
    for _ in range(iteration_count):
        await asyncio.sleep(0)


def get_frames_list(dirnames):
    return [
        load_frame_from_file(join(dirnames, file))
        for file in listdir(dirnames)
        if isfile(join(dirnames, file))
    ]


async def animate_rocket(canvas, start_row, start_column, frames):
    frames_cycle = itertools.cycle(frames)
    height, width = canvas.getmaxyx()
    border_size = 1

    current_frame = next(frames_cycle)
    frame_size_y, frame_size_x = get_frame_size(current_frame)
    frame_pos_x = round(start_column) - round(frame_size_x / 2)
    frame_pos_y = round(start_row) - round(frame_size_y / 2)

    while True:
        direction_y, direction_x, _ = read_controls(canvas)

        frame_pos_x += direction_x
        frame_pos_y += direction_y

        frame_x_max = frame_pos_x + frame_size_x
        frame_y_max = frame_pos_y + frame_size_y

        field_x_max = width - border_size
        field_y_max = height - border_size

        frame_pos_x = min(frame_x_max, field_x_max) - frame_size_x
        frame_pos_y = min(frame_y_max, field_y_max) - frame_size_y
        frame_pos_x = max(frame_pos_x, border_size)
        frame_pos_y = max(frame_pos_y, border_size)

        draw_frame(canvas, frame_pos_y, frame_pos_x, current_frame)
        canvas.refresh()

        await go_to_sleep(0.3)

        draw_frame(
            canvas,
            frame_pos_y,
            frame_pos_x,
            current_frame,
            negative=True
        )
        current_frame = next(frames_cycle)


def load_frame_from_file(filename):
    with open(filename, 'r') as fd:
        return fd.read()


def stars_generator(height, width, number=50):
    for star in range(number):
        y_pos = random.randint(1, height - 2)
        x_pos = random.randint(1, width - 2)
        symbol = random.choice(['+', '*', '.', ':'])
        yield y_pos, x_pos, symbol


async def blink(canvas, row, column, symbol='*', offset=1):
    while True:
        if offset == 0:
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await go_to_sleep(2)
            offset += 1
        if offset == 1:
            canvas.addstr(row, column, symbol)
            await go_to_sleep(0.3)
            offset += 1
        if offset == 2:
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await go_to_sleep(0.5)
            offset += 1
        if offset == 3:
            canvas.addstr(row, column, symbol)
            await go_to_sleep(0.3)
            offset = 0


def main(canvas):
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)

    height, width = canvas.getmaxyx()

    coroutines = [blink(canvas, row, column, symbol, random.randint(0, 3))
                  for row, column, symbol in stars_generator(height, width)
                  ]

    start_row = height - 2
    start_col = width / 2
    coroutines.append(fire(canvas, start_row, start_col))

    rocket_frames = get_frames_list(ROCKET_FRAMES_DIR)

    start_rocket_row = height / 2
    coro_rocket_anim = animate_rocket(
        canvas,
        start_rocket_row,
        start_col,
        rocket_frames
    )
    coroutines.append(coro_rocket_anim)

    garbage_frames = get_frames_list(GARBAGE_FRAMES_DIR)
    garbage_coro = [
        fly_garbage(canvas, (column * 10) + 5, frame)
        for column, frame in enumerate(garbage_frames)
    ]

    coroutines.extend(garbage_coro)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)

        if len(coroutines) == 0:
            break
        time.sleep(0.05)
        canvas.refresh()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(main)
