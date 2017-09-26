#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import print_function

import argparse
import base64
import hashlib
import sys
import time

FLDBASE = 8
FLDSIZE_X = (FLDBASE * 2 + 1)
FLDSIZE_Y = (FLDBASE + 1)

START = ((FLDSIZE_X / 2), (FLDSIZE_Y / 2))

# Initialize FIELDS to fill x and y with 0s
FIELDS = [[0 * j for j in range(9)] for i in range(17)]

BISHOP = u'♝'
START_CHAR = 'S'
END_CHAR = 'E'

AUGMENTATION_STRING = {
    'ascii': ' .o+=*BOX@%&#/^',
    'block': [
        ' ',
        u'\u2591',
        u'\u2592',
        u'\u2593',
        u'\u2582',
        u'\u2584',
        u'\u2586',
        u'\u259a',
        u'\u259e',
        u'\u259b',
        u'\u259c',
        u'\u2599',
        u'\u259f',
        u'\u2587',
        u'\u2588',
    ],
    'drawing': [
        ' ',
        u'\u2551',
        u'\u2562',
        u'\u2553',
        u'\u2564',
        u'\u2555',
        u'\u2566',
        u'\u2557',
        u'\u2568',
        u'\u2559',
        u'\u256a',
        u'\u255b',
        u'\u256c',
        u'\u255d',
        u'\u256e',
    ],
}

AUGMENTATION_GROUP = 'ascii'


def get_augmentation_string():
    return AUGMENTATION_STRING[AUGMENTATION_GROUP]


def md5sum(datum):
    """
    Returns md5 checksum for chunk
    """
    m = hashlib.md5()
    m.update(datum)
    return m.hexdigest()


def to_pairs(data):
    """
    Turns list of data into tuples of data pairs.
    """
    return zip(data[::2], data[1::2])


def to_moves(data):
    """
    Takes a list of tuples representing hex digits and returns a list of
    little-endian binary pairs representing movements.
    """
    moves = []
    for bit_pair in data:
        bits = '{:08b}'.format(int(''.join(bit_pair), 16))
        moves += to_pairs(bits)[::-1]
    return moves


def field_char(x, y, bishop, end=False):
    if x == bishop[0] and y == bishop[1]:
        if end:
            return END_CHAR
        return BISHOP

    if x == START[0] and y == START[1]:
        return START_CHAR

    augmentation_string = get_augmentation_string()
    augmentation_offset = min(FIELDS[x][y], len(augmentation_string))

    char = augmentation_string[augmentation_offset]
    return u'{}'.format(char)


def draw_box(bishop, end=False):
    # Top
    border = ['-' for i in range(0, FLDSIZE_X)]
    print('+' + ''.join(border) + '+')

    # Body
    for y in range(0, FLDSIZE_Y):
        row = '|'
        for x in range(0, FLDSIZE_X):
            if x == bishop[0] and y == bishop[1]:
                FIELDS[x][y] += 1
            row += field_char(x, y, bishop, end)
        row += '|'
        print(row)

    # Bottom
    print('+' + ''.join(border) + '+')

    # Reset to top of box output:
    #   \r moves to left most column (carriage return)
    #   Esc[valueA moves up `value` lines. FLDSIZE_Y + top and bottom rows
    #   no new line at end of string
    print('\r\x1b[{}A'.format(FLDSIZE_Y + 2), end='')


def move_bishop(bishop, move):
    move = int(''.join(move), 2)

    if move & 0x1 > 0:
        x = bishop[0] + 1
    else:
        x = bishop[0] - 1

    if move & 0x2 > 0:
        y = bishop[1] + 1
    else:
        y = bishop[1] - 1

    x = max(x, 0)
    y = max(y, 0)
    x = min(x, FLDSIZE_X - 1)
    y = min(y, FLDSIZE_Y - 1)

    return (x, y)


def to_rgb(color):
    return int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)


def to_ansi_rgb(color):
    r, g, b = to_rgb(color)
    return '\x1b[38;2;{};{};{}m'.format(r, g, b)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '-e', '--base64-encoded', action='store_true',
        help='Input is base64 encoded')
    ap.add_argument(
        '-b', '--block-chars', action='store_true',
        help='Use block-chars')
    ap.add_argument(
        '-d', '--drawing-chars', action='store_true',
        help='Use drawing-chars')
    ap.add_argument(
        '-c', '--colors', action='store_true',
        help='Use colors')
    ap.add_argument(
        '-s', '--sleep', type=float, default=0.5,
        help='Time to sleep between drawing iterations')

    return ap.parse_args()


def set_augmentation_group(args):
    global AUGMENTATION_GROUP

    if args.block_chars:
        AUGMENTATION_GROUP = 'block'
        return

    if args.drawing_chars:
        AUGMENTATION_GROUP = 'drawing'
        return


if __name__ == '__main__':
    args = parse_args()
    base = sys.stdin.read().strip()

    if args.base64_encoded:
        base = base64.decodestring(base)

    md5 = md5sum(base)
    print(md5)

    moves = to_moves(to_pairs(md5))

    try:
        if args.colors:
            print(to_ansi_rgb(md5[:6]), end='')

        set_augmentation_group(args)

        bishop = START

        draw_box(bishop)
        for move in moves:
            bishop = move_bishop(bishop, move)
            draw_box(bishop)
            time.sleep(args.sleep)

        draw_box(bishop, end=True)
    finally:
        # go to bottom of screen
        print('\x1b[0m\x1b[{}B'.format(FLDSIZE_Y + 2), end='')
