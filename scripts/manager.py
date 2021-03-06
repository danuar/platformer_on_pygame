import logging
import time
from typing import List, Dict, Tuple

import pygame as pg

from threading import Thread
from array import array

from . import *


class GameManager:

    def __init__(self):
        # Default variable
        self.is_init = False
        self.FPS = 60
        Weapon.list_all_player = Gun.list_all_player = self.list_all_player = []
        self.pos = self.pressed = None
        self.last_thread: Thread = None
        self.is_end = False

        # Debug variable
        self.array_fps = array('d', [])
        self.last_time = time.time()

        # Инициализация всех модулей pygame
        pg.init()
        pg.display.init()
        pg.mixer.init()
        pg.font.init()

        # Создание основного дисплея
        self.display = pg.display.set_mode(get_config_value('settings', 'window_size'), pg.DOUBLEBUF | pg.HWSURFACE | pg.RESIZABLE)
        Weapon.surface = Gun.surface = self.display
        self.background = pg.image.load('world/background.jpg').convert()

        self.clock = pg.time.Clock()
        self.DEBUG = get_config_value('game', 'debug')
        Timer.DEBUG = self.DEBUG

        # Шрифты
        self.game_font = pg.font.match_font(pg.font.get_fonts()[96])
        self.default_font = pg.font.Font(self.game_font, 25)
        Player.font = self.default_font

        # Игрок
        self.param_create_player = {
            'init': [((50, 90),), {'speed_animation': 0.15}],
            'load': [('heroes1', (0, 0, 255)), {}]
        }
        self.pl1 = self.create_player()

        # Создание базовых векторов в синглтоне с нулевой коородинатой в левой верхней точке
        self.base_vector = BaseVector(*pg.display.get_window_size())

        # Интерфейс
        self.pl1.add_element_interface(pg.image.load('resources/interface/doska.png'),
                                       pg.image.load('resources/interface/frame.png'))
        self.chat = Chat(self.display, (0, 0, 0), (0, 20), (self.base_vector.x.x // 2, 0), self.pl1.name)
        self.camera = Camera(self.pl1, (-5000, -5000), (5000, 5000), [i // 2 for i in pg.display.get_window_size()])
        self.list_all_weapon = [
            Weapon('Меч', 'sword.png', 20),
            Gun('Автомат', 'gun1.png', 10, self.base_vector * (.3, 0), (.5, .5)),
            Gun('Снайперка', 'sniper_rifle.png', 70, (2000, 300), default_scatter=3, increase_scatter=200,
                shot_in_minutes=10, magazine=5, time_reload=3, max_scatter=1000)
        ]
        logging.info('Init game')

        # Создание препятсвий
        im = pg.image.load('world/dir.png').convert()
        pos = Let.create_lets_to_y(im, 20, (0, 1500), True)
        pos = Let.create_lets(im, 20, pos, True, True)
        pos = Let.create_lets_to_x(im, 30, pos)
        pos = Let.create_lets_to_y(im, 40, pos, True)

        self.is_create_server = Menu((21, 21, 21), (32, 32, 32), (600, 100), (14, 255, 14 * 16 + 13)).run()
        # Server
        if self.is_create_server:
            server = Server()
            pg.display.set_caption('Server')
            self.manager = ConnectionManager(self.chat, self.param_create_player, server)
            Thread(target=self.manager.server.loop, daemon=True).start()
            print("server", self.pl1)

        else:
            client = Client()
            pg.display.set_caption('Client')
            #  Debug
            self.chat.name = self.pl1.name = 'Player11'
            self.param_create_player['init'][1]['name'] = 'Player11'
            _ = list(self.param_create_player['load'][0])
            _[1] = (0, 0, 0)
            self.param_create_player['load'][0] = _

            self.manager = ConnectionManager(self.chat, self.param_create_player, client_=client)

        Chat.manager = self.manager
        self.last_thread.join()

    def create_player(self, param_create=None):
        if param_create is None:
            param_create = self.param_create_player
        pl = Player(self.display, *param_create['init'][0], **param_create['init'][1])
        self.list_all_player.append(pl)
        self.last_thread = Thread(target=pl.load_animation, args=param_create['load'][0],
                                  kwargs=param_create['load'][1])
        self.last_thread.start()
        return pl

    def create_other_player(self, mess_client, is_add_player_in_entity=True):
        # Add new player
        if type(mess_client) == tuple and mess_client[0] == 'player':
            print("client" if self.is_create_server else "server", self.pl1.name, mess_client[1])
            logging.info(f'Create new {"client" if self.is_create_server else "server"} player')
            param = mess_client[1]
            param['init'][1]['is_centering_camera'] = False
            new_player = self.create_player(param)
            if is_add_player_in_entity:
                self.pl1.entity.append(new_player)
                new_player.entity.append(self.pl1)
            self.last_thread.join()

    def debug(self):
        if self.DEBUG:
            li = [str(round(i, 3)) for i in [self.clock.get_fps()]]
            self.array_fps.append(float(li[0]))
            if len(self.array_fps) > 200:
                del self.array_fps[0]
            fps = f'[↑{max(self.array_fps)}, ↓{min(self.array_fps)}, /{round(sum(self.array_fps) / len(self.array_fps), 3)}]'
            st = f'pos:<{self.pl1.rect.center}> fps: {li[0]} {fps}'
            st1 = str(self.pl1)
            if len(self.list_all_player) > 1:
                st1 = str(self.list_all_player[1])
            if self.is_create_server and time.time() - self.last_time > 2:
                print('Server:', self.pl1.entity)
                self.last_time = time.time()
            elif time.time() - self.last_time > 2:
                print('Client:', self.pl1.entity)
                self.last_time = time.time()
            self.update_text([st, st1] + [str(w) for w in self.list_all_weapon])

    def create_text_obj(self, text: str, font: pg.font.Font = None, color=(255, 0, 0), **kwargs_rect
                        ) -> Tuple[pg.Surface, pg.Rect]:
        if font is None:
            font = self.default_font
        surface = font.render(text, 1, color)
        rect = surface.get_rect(**kwargs_rect)
        return surface, rect

    def update_text(self, it: Tuple[str, str, str]) -> None:
        pos = list(self.base_vector * (1, 0))
        for text in it:
            s, r = self.create_text_obj(text, topright=pos)
            self.display.blit(s, r)
            pos[1] += s.get_size()[1]

    def update_world(self):
        for weapon in self.list_all_weapon:
            weapon.attack(self.pressed, self.pos)
            weapon.gravity()
        for player in self.list_all_player:
            player.animation()
            player()
            if len(self.list_all_player) > 1 and player.name == self.list_all_player[1].name:
                if player.health < 0:
                    print(player)
                    player.death()
        self.camera.move()

    def blit_world(self):
        # Отрисовка
        with Timer('Отрис преп'):
            self.pl1.draw_let()
        with Timer('Отрис Игрока'):
            for pl in self.list_all_player:
                pl.blit()
        with Timer('Отрис Оружия'):
            for weapon in self.list_all_weapon:
                weapon.blit()

        # Интерфейс
        with Timer('Отрис интерфейса'):
            for pl in self.list_all_player:
                pl.draw_interface()
        with Timer('Отрис сообщений'):
            self.chat.draw_message()

        # Обновление дисплея и добавление заднего фона
        with Timer('Обнов дисплея'):
            self.last_thread = Thread(target=self.update_display, args=(self.display, self.new_background()))
            self.last_thread.start()

    @staticmethod
    def update_display(display, background):
        pg.display.flip()
        display.blit(background, (0, 0))
        Timer.update()

    def new_background(self):
        return pg.transform.scale(self.background, pg.display.get_window_size())

    @staticmethod
    def pickle_event(queue_event: List[pg.event.Event]) -> List[Dict[str, object]]:
        res = []
        for i in queue_event:
            dict_ = i.__dict__
            dict_['type'] = i.type
            res.append(dict_)
        return res

    @staticmethod
    def unpickle_event(event_dict: List[Dict[str, object]]) -> List[pg.event.Event]:
        res = []
        for i in event_dict:
            typing = i['type']
            del i['type']
            res.append(pg.event.Event(typing, i))
        return res

    def run(self):
        while not self.is_end:

            with Timer('События'):
                if self.chat.is_lock_main_loop_event:
                    self.chat.update_input()
                else:
                    self.loop_control()
            # Server
            with Timer('Сообщения'):
                self.create_message_for_conn()
            with Timer('Сервер'):
                messages = self.manager.update()
                self.handling_messages(messages)
            with Timer('Обновление мира'):
                self.update_world()
            with Timer('Ожидание потока'):
                self.last_thread.join()
            with Timer('Дебаг'):
                self.debug()
            self.blit_world()
            with Timer('Время'):
                self.clock.tick(60)

    def handling_messages(self, messages):
        for message in messages:
            if len(self.list_all_player) > 1:
                self.handling_message(message)
            self.create_other_player(message)

    def get_weapon(self, name_weapon: str):
        for w in self.list_all_weapon:
            if w.name == name_weapon:
                return w
        return None

    def handling_message(self, message):
        if message[0] == 'event_list':
            self.list_all_player[1].event_list = message[1]
        elif message[0] == 'center':
            self.list_all_player[1].rect.center = message[1]
        elif message[0] == 'pos':
            self.pos = message[1]
        elif message[0] == 'pressed':
            self.pressed = message[1]
        elif message[0] == 'event_queue':
            self.loop_control(self.list_all_player[1], self.unpickle_event(message[1]))
        elif message[0] == 'list_bullet':
            gun = sorted(self.list_all_weapon, key=lambda x: type(x) != Gun)[0]
            if type(gun) != Gun or gun.player is None: return
            gun.list_bullet += Bullet.create_bullet_in_queue(message[1], gun.player.entity)
        elif message[0] == 'health':
            self.pl1.health = message[1]
        elif message[0] == 'is_up':
            weapon_need = self.get_weapon(message[1])
            weapon_now = self.list_all_player[1].get_weapon_now()
            if weapon_now is None != weapon_need is None:
                if weapon_need:
                    weapon_need.assign_weapon_player(self.list_all_player[1])
                else:
                    weapon_now.is_up = False

    def create_message_for_conn(self):
        info = [('pos', pg.mouse.get_pos()), ('pressed', pg.mouse.get_pressed()), ('event_list', self.pl1.event_list),
                ('center', self.pl1.rect.center), ('list_bullet', Bullet.clear_queue()),
                ('is_up', self.pl1.get_weapon_now(True)), ('health', self.list_all_player[-1].health)]
        last_mess = self.manager.get_message()
        if (not (last_mess is None or last_mess == 'default_message')) and type(last_mess) == tuple:
            info.insert(0, last_mess)
        elif isinstance(last_mess, list):
            for mess in last_mess:
                if mess[0] not in ['pos', 'pressed', 'event_list', 'center', 'list_bullet']:
                    info.insert(0, mess)
        self.manager.set_message(info)

    def create_message_event(self, event_queue):
        last_mess = self.manager.get_message()
        if last_mess is None or last_mess == 'default_message':
            next_mess = ('event_queue', self.pickle_event(event_queue))
        elif type(last_mess) == tuple and last_mess[0] == 'event_queue':
            next_mess = ('event_queue', self.pickle_event(event_queue) + last_mess[1])
        else:
            next_mess = last_mess
        self.manager.set_message(next_mess)

    def loop_control(self, player: Player = None, event_queue: List[pg.event.Event] = None):
        if player is None:
            player = self.pl1
        if event_queue is None:
            event_queue = pg.event.get()
            if event_queue:
                self.create_message_event(event_queue)

        # Цикл событий
        for i in event_queue:
            if i.type == pg.WINDOWRESIZED:
                self.base_vector.update(pg.display.get_window_size())
                self.camera.update_size_window()
                self.pl1.update_element_interface()
            if i.type == pg.QUIT:  # Выход
                logging.info('Exit in main loop')
                self.is_end = True
            elif i.type == pg.KEYDOWN:
                if i.unicode.isdigit() and i.unicode != '0':
                    player.weapon_now = int(i.unicode) - 1
                else:
                    if i.key == pg.K_q and player.get_weapon_now() is not None:
                        player.get_weapon_now().is_up = False
                    if i.key == pg.K_t and player == self.pl1:
                        self.chat.create_input()
                    player.control(i)
                    for weapon in self.list_all_weapon:
                        weapon(i.key, player)
            elif i.type == pg.KEYUP and i.key in player.event_list:
                # Удаление опущенных клавиш
                del player.event_list[player.event_list.index(i.key)]
            elif i.type == pg.MOUSEBUTTONDOWN:
                if i.button == 4:
                    player.weapon_now += 1
                    if player.weapon_now > 8: player.weapon_now = 0
                elif i.button == 5:
                    player.weapon_now -= 1
                    if player.weapon_now < 0: player.weapon_now = 8
