import sys
import time
from configparser import ConfigParser
import datetime
from typing import Iterable

import pygame as pg
import re

PATH = 'GameProperty.ini'
if __name__ == '__main__':
    PATH = 'C:/Users/User/PycharGame/GameProperty.ini'

config = ConfigParser()
config.read(PATH)


def get_config_value(section: str, option: str):
    return _transform_str_to_type(config.get(section, option), option)


def _transform_str_to_type(res: str, option=None) -> object:
    st = res
    if st.isdigit():
        res = int(st)
    elif st == 'True' or st == 'False':
        res = True if st == 'True' else False
    elif re.match(r"[0-9]?\.[0-9]?", st):
        res = float(st)
    elif res.count('(') and res.count(')') and option != 'name':
        arr_obj = []
        start_st = st
        while True:
            if start_st.count('('):
                arr_obj.append(_transform_str_to_type(start_st[start_st.find('(')+1:start_st.find(',')].strip()))
                start_st = start_st[start_st.find(',')+1:]
            elif start_st.count(','):
                arr_obj.append(_transform_str_to_type(start_st[:start_st.find(',')].strip()))
                start_st = start_st[start_st.find(',') + 1:]
            else:
                arr_obj.append(_transform_str_to_type(start_st[:start_st.find(')')].strip()))
                break
        res = tuple(arr_obj)
    return res


def set_config_value(section: str, option: str, value):
    config.set(section, option, str(value))
    with open(PATH, 'w') as f:
        config.write(f)


class Chat:
    message_array = []
    manager = None

    def __init__(self, surface, color, pos_start, pos_end, player_name, size_font=30, time_blit=30, ceil_message=250):
        self.ceil_message = ceil_message
        self.time_blit = time_blit
        self.size_font = size_font
        self.name = player_name
        self.disp = surface
        self.color = color
        self.size = pos_start, pos_end
        self.exit_chat = pg.K_ESCAPE
        self.button_send_message = 13  # Обозначает enter
        self.message = ''
        self.surf = pg.Surface([abs(i - j) for i, j in reversed(self.size)])
        self._gen_anim = self.draw_cursor()
        self.pos_mess = (pos_start[0], pos_start[1])
        self.is_lock_main_loop_event = False
        self._gen = None

    def create_input(self):
        self.is_lock_main_loop_event = True
        self._gen = self._input()

    def update_input(self):
        return next(self._gen)

    def _input(self):
        self.disp.blit(self.surf, [min(*i) for i in zip(self.size)])
        font = pg.font.Font(None, self.size_font)
        flag = True
        pos_cursor = 0
        while flag:
            surf = font.render(self.message[:pos_cursor], 1, (255, 0, 0))
            surf_before_cursor = font.render(self.message[pos_cursor:], 1, (255, 0, 0))
            pos = (surf.get_size()[0], 0)
            self.surf.fill(self.color)
            self.surf.blit(surf, (0, 0))
            self.surf.blit(next(self._gen_anim), pos)
            self.surf.blit(surf_before_cursor, pos)
            self.disp.blit(self.surf, [min(*i) for i in zip(self.size)])
            for i in pg.event.get():
                if i.type == pg.QUIT:
                    sys.exit()
                if i.type == pg.KEYDOWN:
                    if i.key == self.exit_chat:
                        flag = False
                    elif i.key == self.button_send_message:
                        res = self.send_message()
                        if res: yield res
                        self.message = ''
                    elif i.key == pg.K_BACKSPACE and pos_cursor > 0:
                        self.message = self.message[:pos_cursor-1] + self.message[pos_cursor:]
                        pos_cursor -= 1
                    elif i.key == pg.K_RIGHT and pos_cursor < len(self.message):
                        pos_cursor += 1
                    elif i.key == pg.K_LEFT and pos_cursor > 0:
                        pos_cursor -= 1
                    elif i.key not in [pg.K_BACKSPACE, 13, pg.K_DELETE, pg.K_TAB, 1073741912]:
                        self.message = self.message[:pos_cursor] + i.unicode + self.message[pos_cursor:]
                        if i.unicode: pos_cursor += 1
            yield True
        self.is_lock_main_loop_event = False
        yield False

    def draw_message(self):
        pos = list(self.pos_mess)
        for i in reversed(self.message_array):
            if pos[1] > self.ceil_message: break
            is_alive = i.send(pos)
            pos[1] += self.size_font*.7
            if is_alive is False:
                self.del_message(i)

    def draw_cursor(self):
        surf = pg.Surface((1, self.size_font))
        surf.fill((255, 255, 255))
        while True:
            for i in range(30):
                yield surf
            for j in range(30):
                yield pg.Surface((0, 0))

    def send_message(self, translate_message: bool = True):
        if self.message[:6] == '<skin>':
            return _transform_str_to_type(self.message[6:])
        st = str(datetime.datetime.now().time())
        st = f'[{st[:st.find(".")]}] {self.name}: {self.message}'
        if translate_message and self.manager:
            self.manager.chat_update(self.name, self.message)
        self.add_message(self.__message(self.time_blit, st))
        next(self.message_array[-1])  # Инициализируем корутину

    @classmethod
    def add_message(cls, message: str):
        cls.message_array.append(message)

    @classmethod
    def del_message(cls, message: Iterable):
        if message in cls.message_array:
            del cls.message_array[cls.message_array.index(message)]
        else:
            return False

    def __message(self, time_blit, text, color_text=(255, 0, 0)):
        font = pg.font.Font(None, round(self.size_font*.9))
        t_0 = time.time()
        while time.time() - t_0 <= time_blit:
            pos = (yield)
            self.disp.blit(font.render(text, 1, color_text), pos)
        yield False





