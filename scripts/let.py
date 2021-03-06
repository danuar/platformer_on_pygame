from typing import Tuple

import pygame as pg
from .player import Player
from .weapon import Weapon
from .basic import BasicClass


class Let(BasicClass):

    def __init__(self, surface: pg.Surface, top_left=(0, 0)):
        super().__init__()
        Player.group_let.append(self)
        Weapon.group_let.append(self)
        self.frame_image = surface
        self.rect = surface.get_rect(topleft=top_left)

    @staticmethod
    def create_lets(surface: pg.Surface, quantity: int, start_pos: Tuple[int, int], move_x=False, move_y=False,
                    reverse_x=False, reverse_y=False):
        x, y = start_pos
        w, h = surface.get_size()
        for i in range(quantity):
            Let(surface, (x, y))
            if move_x: x += w if not reverse_x else -w
            if move_y: y += h if not reverse_y else -h
        return x, y

    @staticmethod
    def create_lets_to_x(surface: pg.Surface, quantity: int, start_pos: Tuple[int, int], reverse=False):
        return Let.create_lets(surface, quantity, start_pos, move_x=True, reverse_x=reverse)

    @staticmethod
    def create_lets_to_y(surface: pg.Surface, quantity: int, start_pos: Tuple[int, int], reverse=False):
        return Let.create_lets(surface, quantity, start_pos, move_y=True, reverse_y=reverse)
