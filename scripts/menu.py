import sys
import logging
from typing import Tuple

import pygame as pg

from .basic import GameObject


class Menu:

    def __init__(self, color_background, color_button, size_button, color_text):
        logging.info('Create Menu')
        self.color_background, self.color_text = color_background, color_text
        self.size_button = size_button
        self.button_create = pg.Surface(size_button)
        self.button_join = pg.Surface(size_button)
        self.button_join.fill(color_button)
        self.button_create.fill(color_button)
        self.surface = pg.display.get_surface()
        self.font = pg.font.Font(None, (size_button[0] + size_button[1])//12)
        self.center = self.get_receive_half(size_button)
        self.button_join.blit(
            *self.get_surface_and_rect(self.font.render('Присоединиться к игре', 1, self.color_text), self.center))
        self.button_create.blit(
            *self.get_surface_and_rect(self.font.render('Создать игру', 1, self.color_text), self.center))
        self.set_default_button()

    def run(self):
        while True:

            surf1, rect1 = self.get_surface_and_rect(self.button_join_now, self.get_receive_half(pos_y=.2))
            surf2, rect2 = self.get_surface_and_rect(self.button_create_now, self.get_receive_half(pos_y=.7))
            self.surface.blit(surf1, rect1)
            self.surface.blit(surf2, rect2)
            pg.display.flip()
            self.surface.fill(self.color_background)

            for i in pg.event.get():
                if i.type == pg.QUIT:
                    sys.exit()
                if i.type in [1025, 1026] and i.button == 1:
                    if i.type == pg.MOUSEBUTTONUP:
                        if rect1.collidepoint(*i.pos):
                            pg.mouse.set_visible(False)
                            logging.info(f'Choice join server')
                            return False
                        if rect2.collidepoint(*i.pos):
                            pg.mouse.set_visible(False)
                            logging.info(f'Choice create server')
                            return True
                        self.set_default_button()

                    elif i.type == pg.MOUSEBUTTONDOWN:
                        if rect1.collidepoint(*i.pos):
                            self.button_join_now = self.scale(self.button_join, self.size_button, 0.75)
                        if rect2.collidepoint(*i.pos):
                            self.button_create_now = self.scale(self.button_create, self.size_button, 0.75)

    @staticmethod
    def get_surface_and_rect(surface: pg.Surface, pos_center: Tuple[int, int]) -> Tuple[pg.Surface, pg.Rect]:
        return surface, surface.get_rect(center=pos_center)

    @staticmethod
    def get_receive_half(iter_=None, pos_x=None, pos_y=None, k=.5):
        if iter_ is None:
            iter_ = pg.display.get_window_size()
        res = tuple([round(i * k) for i in iter_])
        if pos_y is not None:
            res = res[0], iter_[1]*pos_y
        if pos_x is not None:
            res = iter_[0]*pos_x, res[1]
        return res

    def set_default_button(self):
        self.button_join_now, self.button_create_now = self.button_join, self.button_create

    def scale(self, default, size, k):
        return pg.transform.scale(default, self.get_receive_half(size, k=k))
