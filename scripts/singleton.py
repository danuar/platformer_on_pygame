import logging

import pygame as pg
from pygame.math import Vector2

from typing import Tuple, List, Any, Union, Iterable


class _Singleton:
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.is_init = False
        return cls.instance


class BaseVector(_Singleton):

    def __init__(self, x_pos_base: int = 0, y_pos_base: int = 0):
        if self.is_init: return
        self.x = Vector2(x_pos_base, 0)
        self.y = Vector2(0, y_pos_base)
        self.__class__.is_init = True

    def __mul__(self, other: Union[Tuple[float, float], Vector2]) -> Tuple[float, float]:
        return (self.x * other[0])[0], (self.y * other[1])[1]

    def __rmul__(self, other: Union[Tuple[float, float], Vector2]) -> Tuple[float, float]:
        return (self.x * other[0])[0], (self.y * other[1])[1]

    def update(self, size: Tuple[int, int]) -> None:
        self.x = Vector2(size[0], 0)
        self.y = Vector2(0, size[1])


class Camera(_Singleton):

    def __init__(self, player, start_map: Tuple[int, int], end_map: Tuple[int, int],
                 pos_player_for_move: Tuple[int, int]):
        if self.is_init: return
        self.start = start_map
        self.end = end_map
        self.pos_pl = pos_player_for_move
        self.player = player
        self.width, self.height = pg.display.get_window_size()
        self.center_camera = self.pos_player = self.pos_camera = self.width//2, self.height//2
        self.__class__.is_init = True

    def move(self):
        self.pos_camera = self.player.rect.topleft
        pos = self.is_not_start_or_end_map(self.player.rect.center)
        if pos is True:
            self.center_camera = self.player.rect.topleft
            self.pos_player = self.width//2, self.height//2
        else:
            self.pos_player = pos

    def is_not_start_or_end_map(self, pos):
        x, y = pos
        x_min, y_min = self.start
        x_max, y_max = self.end
        w, h = self.width // 2, self.height // 2
        bool_list = [x - w >= x_min, x + w <= x_max, y - h >= y_min, y + h <= y_max]
        if all(bool_list):
            return True
        pos = list(pos)
        for i, cor, el in zip(bool_list, [0, 0, 1, 1], [x-x_min, x+w*2-x_max, y-y_min, y+h*2-y_max]):
            if not i: pos[cor] = el
        if all(bool_list[:2]):
            pos[0] = self.pos_player[0]
        if all(bool_list[2:]):
            pos[1] = self.pos_player[1]
        return pos

    @classmethod
    def draw_obj(cls, surface_draw, surface_drawable, top_left_pos: Union[pg.Rect, Tuple[int, int]], is_player: bool = False):
        surface_draw.blit(surface_drawable, cls.get_position_object(top_left_pos, is_player))

    @classmethod
    def get_position_object(cls, top_left_pos: Union[pg.Rect, Tuple[int, int]], is_player: bool = False) -> Tuple[int, int]:
        self = cls.instance
        if type(top_left_pos) == pg.Rect:
            top_left_pos = top_left_pos.topleft
        if is_player:
            pos = self.pos_player
        else:
            diff = [i - j for i, j in zip(self.pos_player, self.pos_camera)]
            pos = (top_left_pos[0] + diff[0], top_left_pos[1] + diff[1])
        return pos

    @classmethod
    def get_pos_camera(cls) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """:return two tuple containing min and max coordinates"""
        self = cls.instance
        x, y = self.center_camera
        w, h = self.width // 2, self.height // 2
        return ((x - w, y - h), (x + w, y + h))

    @classmethod
    def get_rect_camera(cls) -> pg.Rect:
        self = cls.instance
        return pg.display.get_surface().get_rect(center=self.center_camera)

    @classmethod
    def get_pos_player(cls):
        return cls.instance.pos_player

    @classmethod
    def update_size_window(cls):
        cls.instance.width, cls.instance.height = pg.display.get_window_size()


