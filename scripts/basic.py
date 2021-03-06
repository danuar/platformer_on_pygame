import time
from array import array
from typing import Tuple, Iterable
from types import GeneratorType

import pygame as pg

from scripts.singleton import Camera, BaseVector
from collections import deque


class BasicClass:
    group_let = []

    def __init__(self):
        self.surface = None
        self.frame_image = None
        self.list_image = None
        self.is_move_camera = None
        self.size = None
        self.rect = None

    def blit(self, Surface: pg.Surface = None, obj: Tuple[pg.Surface, pg.Rect] = None) -> None:
        if Surface is None: Surface = self.surface
        if obj is None: obj = self.frame_image, self.rect
        if self.is_move_camera == 'player':
            Camera.draw_obj(Surface, *obj, is_player=True)
        elif self.is_move_camera:
            Camera.draw_obj(Surface, *obj)
        else:
            Surface.blit(*obj)

    def define_diff_between_move_and_let(self, x, y):
        num = self.rect.move(x, y).collidelist(self.group_let)
        if num != -1:
            res = self.find_diff_between_rect(self.group_let[num].rect, self.rect)
            x, y = res
        return x, y, num

    def move(self, x, y) -> int:
        """Return index Let crossed with player"""
        x, y, r = self.define_diff_between_move_and_let(x, y)
        self.rect.move_ip(x, y)
        return r

    def load_animation(self, name: str, color: Tuple[int, int, int] = None, path='resources/', name_image='f',
                       expansion='.png', _def_color=(255, 0, 0), distance=0):
        """Указываем путь к папке, где находяться изображения героя, и указываем её имя"""
        try:
            for i in range(1, 999999999):

                self.list_image.append(
                    pg.image.load(path + name + '/' + name_image + str(i) + expansion).convert_alpha())
                if self.size is not None:
                    self.list_image[-1] = pg.transform.scale(self.list_image[-1], self.size)
                if color is not None:
                    p = pg.PixelArray(self.list_image[-1])
                    p.replace(_def_color, color, distance)
                    self.list_image[-1] = p.make_surface()
        except FileNotFoundError as er:
            if i == 1:
                raise er

    def __iter__(self):
        return iter((self.frame_image, self.rect))

    def __getstate__(self):  # Pickling surface
        res = {}
        for key, values in self.__dict__.items():
            if type(values) == pg.Surface:  # Make surface string
                values = (pg.image.tostring(values, 'RGBA'), values.get_size(), 'RGBA')
            elif type(values) == GeneratorType:
                values = key
            elif type(values) in [list, tuple] and pg.Surface in map(type, values):
                values = self.__get_pickle_in_surface_iter(values, lambda x: type(x) == pg.Surface)
            res[key] = values

        return res

    def __setstate__(self, state):
        for key, values in state.items():
            if type(values) == tuple and type(values[0]) == bytes and values[2] == 'RGBA':
                values = pg.image.fromstring(*values)
            elif type(values) == Iterable:
                values = self.__get_pickle_in_surface_iter(
                                        values, lambda x: type(x) == tuple and type(x[0]) == bytes and x[2] == 'RGBA')
            elif key == values:
                if key == 'gen' and self.__dict__.get('inventory', False):
                    self.gen = self._generation_animation()

            self.__dict__[key] = values
        return self.__dict__

    @staticmethod
    def __get_pickle_in_surface_iter(iter_, func):
        res = []
        for i in iter_:
            if func(i):
                i = (pg.image.tostring(i, 'RGBA'), i.get_size(), 'RGBA')
            res.append(i)
        if type(iter_) == tuple:
            return tuple(res)
        return res

    @staticmethod
    def find_diff_between_rect(rect1: pg.Rect, rect2: pg.Rect) -> Tuple[int, int]:
        """Вызывается когда нужно вычислить расстояние между двумя прямоугольниками"""
        pos_x = rect1.left - rect2.right if rect1.left > rect2.right else rect2.left - rect1.right
        pos_y = rect1.top - rect2.bottom if rect1.top > rect2.bottom else rect2.top - rect1.bottom
        if pos_x < 0: pos_x = 0
        if pos_y < 0: pos_y = 0
        return pos_x, pos_y

    @staticmethod
    def scale_k(size_k: Tuple[float, float], surface):
        return pg.transform.scale(surface, [int(s * k) for k, s in zip(size_k, surface.get_size())])

    @staticmethod
    def scheduler_text(text: str, center_text: Tuple[int, int], time_blit: float, size: int, surface_blit: pg.Surface,
                       color=(21, 21, 21), font=None):
        if font is not None:
            font = pg.font.match_font(font)
        surf = pg.font.Font(font, size).render(text, 1, color)
        rect = surf.get_rect(center=center_text)
        t_0 = time.time()
        while time.time() - t_0 <= time_blit:
            surface_blit.blit(surf, rect)

    @staticmethod
    def fill_line(surface, pos_start, pos_end, level_fill, color, color_background=(200, 200, 200), width=4):
        pos_start = Camera.get_position_object(pos_start)
        pos_end = Camera.get_position_object(pos_end)
        pg.draw.line(surface, color_background, pos_start, pos_end, width)
        pos_end = round((pos_end[0] - pos_start[0]) * level_fill/100)+pos_start[0], pos_end[1]
        pg.draw.line(surface, color, pos_start, pos_end, width)


class GameObject(BasicClass):

    def __init__(self, surface, pos_center, name=None):
        super().__init__()
        self.frame_image = surface.convert_alpha()
        self.rect: pg.Rect = self.frame_image.get_rect(center=pos_center)
        self.name = name

    def update(self, pos_center):
        self.rect = self.frame_image.get_rect(center=pos_center)

    def __eq__(self, other):
        return self.name == other.name


class Timer:
    DEBUG = None
    sum_time = 10
    summer = 0
    result = ''
    two_array = [array('d', []) for _ in range(20)]
    count = 0

    def __init__(self, name):
        self.name = name
        self.count = self.count
        self.__class__.count += 1

    def __enter__(self):
        self.t_0 = time.perf_counter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        t = time.perf_counter() - self.t_0
        self.time = t
        self.__class__.summer += t
        arr = self.__class__.two_array[self.count]
        arr.append(t / self.sum_time * 100)
        if len(arr) > 200:
            del arr[0]
        pr = round(sum(arr) / len(arr))
        self.__class__.result += f'{self.name}: {pr}%, '

    @classmethod
    def update(cls):
        cls.sum_time = cls.summer
        font = pg.font.Font(None, 20)
        display = pg.display.get_surface()
        cls.result += 'Sum: ' + str(round(cls.summer, 3))
        surf = font.render(cls.result[:len(cls.result)//2], 1, (255, 0, 0))
        rect = surf.get_rect(topright=BaseVector() * (1, 0.37))
        if cls.DEBUG: display.blit(surf, rect)
        surf = font.render(cls.result[len(cls.result) // 2:], 1, (255, 0, 0))
        rect = surf.get_rect(topright=BaseVector() * (1, 0.4))
        if cls.DEBUG: display.blit(surf, rect)
        cls.count = 0
        cls.summer = 0
        cls.result = ''
