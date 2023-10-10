import asyncio
import curses
import itertools
import random
import time

from fire_animation import fire
from curses_tools import draw_frame, get_frame_size, read_controls


async def animate_frames(canvas, start_row, start_column, frames):
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

        i = 1
        while i < 3:
            await asyncio.sleep(0)
            i += 1

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


def stars_generator(height, width, number):
    for star in range(number):
        y_pos = random.randint(1, height - 2)
        x_pos = random.randint(1, width - 2)
        symbol = random.choice(['+', '*', '.', ':'])
        return y_pos, x_pos, symbol


async def blink(canvas, row, column, symbol):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        i = 1
        while i < random.randint(4, 9):
            await asyncio.sleep(0)
            i +=1

        canvas.addstr(row, column, symbol)
        i = 1
        while i < random.randint(2, 4):
            await asyncio.sleep(0)
            i += 1

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        i = 1
        while i < random.randint(5, 10):
            await asyncio.sleep(0)
            i += 1

        canvas.addstr(row, column, symbol)
        i = 1
        while i < random.randint(2, 4):
            await asyncio.sleep(0)
            i += 1


def main(canvas):
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)

    height, width = canvas.getmaxyx()
    number = 50

    count_coroutine = 1
    coroutines = []

    while count_coroutine < number:
        row, column, symbol = stars_generator(height, width, number)
        coroutine_ = blink(canvas, row, column, symbol)
        coroutines.append(coroutine_)
        count_coroutine +=1

    start_row = height - 2
    start_col = width / 2

    coroutines.append(fire(canvas, start_row, start_col))

    rocket_frame_1 = load_frame_from_file(
        './graphics_files/rocket_frame_1.txt'
    )
    rocket_frame_2 = load_frame_from_file(
        './graphics_files/rocket_frame_2.txt'
    )

    rocket_frames = (rocket_frame_1, rocket_frame_2)
    start_rocket_row = height / 2
    coro_rocket_anim = animate_frames(
        canvas,
        start_rocket_row,
        start_col,
        rocket_frames
    )
    coroutines.append(coro_rocket_anim)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                # time.sleep(0.1)
            except StopIteration:
                coroutines.remove(coroutine)

        if len(coroutines) == 0:
            break
        time.sleep(0.05)
        canvas.refresh()




if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(main)
    # curses.wrapper(draw1)