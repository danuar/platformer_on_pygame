import math
import time
import random
from threading import Thread
from collections import deque
from typing import Tuple, List

from .basic import BasicClass, GameObject
import pygame as pg

from .singleton import BaseVector, Camera


G = 9.8
pg.font.init()
font = pg.font.Font(None, 20)


class Weapon(BasicClass):
    PATH = 'resources/weapon/'
    surface = None
    list_all_player = None

    def __init__(self, name, name_file, damage, spawn=(0, 0), size_k: Tuple[int, int] = None, list_all_player=None, display=None):
        super().__init__()
        self.is_reload = None
        self.is_dir = False
        self.is_attack = False
        self.name = name
        if display is not None:
            self.surface = display
        else:
            self.surface = self.__class__.surface
        self.damage = damage
        self.frame_image = self.image = pg.image.load(self.PATH + name_file).convert_alpha()
        if size_k is not None:
            self.frame_image = self.image = self.scale_k(size_k, self.image)
            self.image = self.image.copy()
        self.rect = self.frame_image.get_rect(topleft=spawn)
        self.icon = None
        if list_all_player is not None:
            self.list_all_player = list_all_player
        else:
            self.list_all_player = self.__class__.list_all_player
        self.is_move_camera = True
        self.is_flip = False
        self.player = None
        self.is_up = False
        self.button_up = pg.K_f
        self.angle = 0
        self.button_attack = 0
        self._is_swing = False

    def _set_default_value(self):
        self.angle = 0
        self._is_swing = False
        self.is_attack = False

    def is_crossing_in_player(self):
        r = self.rect.collidelist([x.rect for x in self.list_all_player])
        return self.list_all_player[r] if r != -1 else False

    def update_weapon(self):
        if self.player.is_flip:
            if not self.is_flip:
                self.frame_image = pg.transform.flip(self.frame_image, 1, 0)
                self.is_flip = True
            self.player.arm = (self.player.arm[0] - 2 * self.player.rect.width + 5, self.player.arm[1])
        elif self.is_flip:
            self.frame_image = pg.transform.flip(self.frame_image, 1, 0)
            self.is_flip = False
        if type(self) == Weapon:
            self.update_sword()

    def update_sword(self):
        pos = self.player.arm  # Изменение координат меча, с изменением угла
        pos = (pos[0] - self.angle, pos[1]) if self.angle > 0 else (pos[0], pos[1] - self.angle)
        if self.is_flip and self.player.is_flip:
            pos = (pos[0] + self.angle, pos[1]) if self.angle > 0 else (pos[0] + self.angle / 1.8, pos[1])
        self.rect: pg.Rect = self.frame_image.get_rect(bottomleft=pos)

    def __call__(self, button, player):
        if button == self.button_up and player == self.is_crossing_in_player() and self.is_up is False:
            self.assign_weapon_player(player)

    def assign_weapon_player(self, player):
        if player.get_weapon_now() is not None:
            player.get_weapon_now().is_up = False
        player.inventory[player.weapon_now] = self
        self.player = player
        self.is_up = True

    def attack(self, pressed=None, pos=None):
        if pressed is None or self.player == self.list_all_player[0]:
            pressed = pg.mouse.get_pressed()
        if pressed[self.button_attack] and self.is_up and not self.is_attack:
            self.is_attack = True
        if self.is_attack:
            num_pl = self.rect.collidelist(self.player.entity)
            if num_pl != -1 and self.player.entity[num_pl].is_death is False and self.player.entity[
                num_pl].is_damage is False:
                self.player.entity[num_pl].is_damage = True
                self.player.entity[num_pl].health -= self.damage
            self.angle += 2 if self._is_swing is False else -5
            if self.angle > 20: self._is_swing = True
            if self.angle < -62:
                self.angle = 0
                self.is_attack = self._is_swing = False
            self.frame_image = pg.transform.rotate(self.image, (90 - self.angle if self.is_flip else self.angle))
        if self.player and self.angle == 0:
            for i in self.player.entity:
                if i.is_damage:
                    i.is_damage = False

    def gravity(self):
        pl = self.is_crossing_in_player()
        text = 'F - Для взаимодействия'
        text = GameObject(font.render(text, 1, (21, 21, 21)), BaseVector() * (.5, .85), self.name)
        if pl is not False and self.is_up is False and pl.is_move_camera == 'player':
            if text not in pl.interface_list:
                pl.interface_list.append(text)
        elif pl is False:
            for player in self.list_all_player:
                for i, t in enumerate(player.interface_list):
                    if t.name == self.name:
                        del player.interface_list[i]
        self.move(0, G)

    @property
    def is_up(self):
        return self._is_up

    @is_up.setter
    def is_up(self, value):
        if value:
            if type(self) == Gun:
                self.is_move_camera = False
            self.frame_image = self.image
            if not self.is_flip == (self.frame_image != self.image):
                self.is_flip = self.frame_image != self.image
            self._is_up = True
        else:
            self.is_move_camera = True
            if type(self) == Gun:
                self.is_reload = self.lock = False
                self.surface_aim = None
            self._is_up = False
            if self.player is not None:
                self.update_weapon()
                self._set_default_value()
                self.rect = self.frame_image.get_rect(topleft=self.player.rect.topleft)
                self.player.inventory[self.player.weapon_now] = None
            self.frame_image = self.scale_k((.5, .5), self.image)
            self.rect = self.frame_image.get_rect(center=self.rect.center)

    def blit(self, Surface: pg.Surface = None, obj: Tuple[pg.Surface, pg.Rect] = None) -> None:
        if self.is_up is False or self.player.get_weapon_now() == self:
            super(Weapon, self).blit(Surface, obj)

    def __str__(self):
        return f'<Weapon: {self.name}, camera={self.is_move_camera}, attack={self.is_attack}, up={self.is_up}, ' \
               f'pos={self.rect.center}>'


class Gun(Weapon):
    list_image_fire: Tuple[pg.Surface] = None

    def __init__(self, name, name_file, damage, spawn=(0, 0), size_k: Tuple[int, int] = None, color_aim=(255, 255, 255),
                 default_scatter: int = 75, increase_scatter: int = 15, shot_in_minutes=100, position_fire=(172, -10),
                 speed_bullet=50, max_scatter: int = 180, magazine: int = 30, time_reload=1.5, list_all_player=None,
                 display=None, _rep_color: Tuple[int, int, int] = (17, 17, 17), uncrease_scatter: float = 1,
                 time_start_uncrease: float = 1):
        th = Thread(target=self.load_animation_fire, args=('animation_fire', ))
        super(Gun, self).__init__(name, name_file, damage, spawn, size_k, list_all_player, display)
        self.list_image = []
        th.start()
        self.last_time_attack = time.time()
        if size_k is not None:
            self.pos_fire = tuple([i * j for i, j in zip(position_fire, size_k)])
        else:
            self.pos_fire = position_fire
        self.time_start_uncrease = time_start_uncrease
        self.uncrease_scatter = uncrease_scatter
        self.size_aim = (default_scatter - 1, default_scatter - 1)
        self.default_scatter = self.scatter_now = default_scatter
        self.rep_color = _rep_color
        self.length_mag = self.magazine = magazine
        self.increase_scatter = increase_scatter
        self.speed = 60 / shot_in_minutes
        self.time_reload = time_reload
        self.max_scatter = max_scatter
        self.speed_bullet = speed_bullet
        self.color_aim = color_aim
        self.button_reload = pg.K_r
        surf = self.image.copy()
        surf.scroll(10, 0)
        self.surf_ammunition_interface = pg.image.load('resources/interface/ammunition.png').convert_alpha()
        self.icon = pg.transform.rotate(self.scale_k((.4, .4), surf), 45)
        self.fire_rect = self.gen = self.pos_muzzle = self.vec2d = None
        self.is_anim = self.is_stop_anim = self.is_reload = self.lock = False
        self.list_bullet = []
        self.rect_aim: pg.Rect = pg.Rect(10, 20, 23, 66)
        self.last_time_reload = time.time()
        self.surface_aim: pg.Rect = None
        self.mouse_pos = None
        th.join()

    def __call__(self, button, player):
        super(Gun, self).__call__(button, player)
        if self.button_reload == button and self.is_up and not self.is_reload:
            self.is_reload = True
            self.lock = True
            self.last_time_reload = time.time()

    def load_animation_fire(self, name: str, color: Tuple[int, int, int] = None, path='resources/weapon/',
                            name_image='fire', expansion='.png', _def_color=(255, 0, 0), distance=0):
        if self.__class__.list_image_fire is not None:
            self.list_image = self.list_image_fire
            return
        super().load_animation(name, color, path, name_image, expansion, _def_color, distance)
        self.__class__.list_image_fire = self.list_image

    def update_weapon(self):
        super(Gun, self).update_weapon()
        if self.is_anim:
            next(self.gen)
        x, y = [i[1] - i[0] for i in zip(self.define_pos(True), self.mouse_pos)]
        x1, y1 = [i[1] - i[0] for i in zip(self.get_rect_player(True).center, self.mouse_pos)]
        self.vec2d = vec2d = pg.Vector2(x, y)
        self.angle = angle = vec2d.angle_to(BaseVector().x)
        norm_angle = pg.Vector2(x1, y1).angle_to(BaseVector().x)
        coord_2 = (90 < angle or angle < -90)
        if (-90 < norm_angle < 90) and self.is_flip:
            self.is_flip = self.player.is_flip = False
        elif (90 < norm_angle or norm_angle < -90) and not self.is_flip:
            self.is_flip = self.player.is_flip = True

        if vec2d.length() > 20 and ((coord_2 and self.is_flip) or (-90 < angle < 90 and not self.is_flip)):
            if coord_2 and self.is_flip:
                angle += 180
            surface = pg.transform.flip(self.image, 1, 0) if self.is_flip else self.image
            self.frame_image = pg.transform.rotate(surface, angle)
        self.rect = self.frame_image.get_rect(center=self.define_pos())
        self.define_muzzle_pos()
        if self.is_reload:
            if time.time() - self.last_time_reload >= self.time_reload:
                self.is_reload = self.lock = False
                self.length_mag = self.magazine
        # Реализация разброса
        scatter = round(self.scatter_now / 250 * (vec2d.length() / 2))
        self.scatter(scatter)

    def scatter(self, scatter_size: int):

        if scatter_size < 15:
            scatter_size = 15
        size = (scatter_size, scatter_size)
        self.rect_aim = pg.Surface(size).get_rect(center=self.mouse_pos)
        if size != self.size_aim:
            self.size_aim = size
            if self.player != self.list_all_player[0]: return
            self.draw_aim()

    def draw_aim(self) -> pg.Surface:
        """Отрисовка прицела и возврат поверхности содержащий прицел"""
        w, h = self.rect_aim.width, self.rect_aim.height
        size = [w / 18, h / 18]
        for i in range(2):
            if size[i] == 0: size[i] = 1
        surface = pg.Surface((w, h))
        surface.set_colorkey((0, 0, 0))
        width = math.ceil(size[0] / 6)
        pg.draw.circle(surface, self.color_aim, (w / 2, h / 2), (size[0] + size[1]) / 4)
        pg.draw.line(surface, self.color_aim, (w / 2, h), (w / 2, h - size[0] * 4), width)
        pg.draw.line(surface, self.color_aim, (w / 2, 0), (w / 2, size[0] * 4), width)
        pg.draw.line(surface, self.color_aim, (w, h / 2), (w - size[1] * 4, h / 2), width)
        pg.draw.line(surface, self.color_aim, (0, h / 2), (size[1] * 4, h / 2), width)
        self.surface_aim = surface
        return surface

    def attack(self, pressed=None, pos=None):
        if pressed is None or self.player == self.list_all_player[0]:
            pressed = pg.mouse.get_pressed()
        if pos is None or self.player == self.list_all_player[0]:
            self.mouse_pos = pg.mouse.get_pos()
        else:
            self.mouse_pos = pos
        for num, i in enumerate(self.list_bullet):
            if not i.move():
                self.list_bullet.pop(num)
        if self.player is not None and self.player.get_weapon_now() != self or self.lock:
            return
        if pressed[self.button_attack] and self.is_up and not self.is_attack and self.length_mag > 0:

            if self.player != self.list_all_player[0]: return
            # if self.player.rect.colliderect(self.rect_aim):  # Прицел слишком близко к оружию
            #     Thread(target=self.scheduler_text, args=('Выстрел невозможен из-за слишком маленького расстояния',
            #                                              BaseVector() * (.5, .82), 2, 20, self.surface)).start()
            #     return
            self.length_mag -= 1
            self.is_attack = True
            if self.scatter_now + self.increase_scatter <= self.max_scatter:
                self.scatter_now += self.increase_scatter
            self.last_time_attack = time.time()
            self.gen = self.animation_fire()
            next(self.gen)
            # Реализация рандомного направления пуль относительно разброса прицела
            random_pos = [random.randint(min(i, j), max(i, j)) for i, j in
                          zip(self.rect_aim.topleft, self.rect_aim.bottomright)]
            self.list_bullet.append(Bullet(self.speed_bullet, self.pos_muzzle, random_pos, self.damage, self.player.entity))
        if self.is_attack:
            if time.time() - self.last_time_attack > self.speed:
                self.is_attack = False
                for _ in self.gen: pass  # Пропускаем анимацию
        if time.time() - self.last_time_attack >= self.time_start_uncrease and self.scatter_now > self.default_scatter:
            self.scatter_now -= self.uncrease_scatter

    def animation_fire(self):
        surf_copy = self.image.copy()
        self.is_anim = True
        for s in self.list_image_fire:
            self.image = surf_copy.copy()
            self.image.blit(s, self.pos_fire)
            yield True
        self.is_anim = False
        self.image = surf_copy
        yield False

    def define_pos(self, is_center=False) -> Tuple[int, int]:
        """Возврат координаты центра вращения оружия"""
        y = pg.display.get_window_size()[1]
        y = 0 if y >= 600 else 5
        pl_rect = self.get_rect_player(is_center)
        return pl_rect.centerx + (-20 if self.is_flip and self.player.is_flip else 20), pl_rect.centery - y

    def get_rect_player(self, is_center=False) -> pg.Rect:
        if is_center:
            return self.player.frame_image.get_rect(topleft=Camera.get_pos_player())
        return self.player.frame_image.get_rect(topleft=Camera.get_pos_player() if self.player == self.list_all_player[0]
                                                        else Camera.get_position_object(self.player.rect.topleft))

    def define_muzzle_pos(self):
        w = self.image.get_size()[0] / 2
        x, y = self.define_pos()
        rad = math.radians(self.angle)
        self.pos_muzzle = [x + math.cos(rad) * w, y - math.sin(rad) * w]

    def install_skin(self, color: Tuple[int, int, int]) -> None:
        pix_array = pg.PixelArray(self.image)
        pix_array.replace(self.rep_color, color, distance=0.01)
        self.image = pix_array.make_surface()

    def blit(self, Surface: pg.Surface = None, obj: Tuple[pg.Surface, pg.Rect] = None) -> None:
        super(Gun, self).blit(Surface, obj)
        if Surface is None: Surface = self.surface
        if self.surface_aim is not None and self == self.player.get_weapon_now():
            pos = BaseVector() * (0, .85)
            size = self.surf_ammunition_interface.get_size()
            surf = pg.font.Font(None, round(size[1] * 1.75)).render(f'{self.length_mag}/{self.magazine}', 1,
                                                                    (240, 240, 240))
            Surface.blit(self.surf_ammunition_interface, pos)
            Surface.blit(surf, (pos[0] + size[0] + 2, pos[1]))
            Surface.blit(self.surface_aim, self.rect_aim)
        for i in self.list_bullet:
            Surface.blit(*i)

    def __str__(self):
        return f'<Gun: {self.name}, camera={self.is_move_camera}, attack={self.is_attack}, up={self.is_up}, ' \
               f'angle={self.angle}, pos={self.pos_muzzle}> time_last_attack={time.time() - self.last_time_attack}'


class Bullet:
    bullet_surface: pg.Surface = None
    queue_bullet_mess = deque()

    def __init__(self, speed, pos_beg, pos_end, damage, entity, surface=None, is_add_queue=True):
        if is_add_queue:
            self.__class__.queue_bullet_mess.append((speed, pos_beg, pos_end, damage))
        if self.bullet_surface is None:
            self.__class__.bullet_surface = pg.image.load('resources/weapon/bullet.png').convert_alpha()
        if surface is None:
            surface = self.bullet_surface
        self.damage = damage
        self.entity = entity
        self.pos_beg = pos_beg
        self.vec = pg.Vector2(*[i[1] - i[0] for i in zip(pos_beg, pos_end)])
        self.surface = pg.transform.rotate(surface, self.vec.angle_to(BaseVector().x))
        self.rect = self.surface.get_rect(center=pos_beg)
        vec = pg.Vector2(self.vec)
        self.vec.scale_to_length(speed)
        self.v = tuple(self.vec)
        vec.scale_to_length(min(surface.get_size()))
        self.move_bullet = tuple(vec)

    def move(self):
        self.point_start = self.rect.center
        self.rect.move_ip(*self.v)
        self.point_end = self.rect.center
        for pl in self.entity:
            if self._collision_rect(pl.rect) or pl.rect.colliderect(self.rect) or self.is_collision(pl.rect):
                pl.health -= self.damage
                return False

        if any([i[1] - i[0] > 3000 for i in zip(self.pos_beg, self.rect.center)]):
            return False
        return True

    @staticmethod
    def create_bullet_in_queue(iter_: List[Tuple[int, Tuple[int, int], pg.Rect]], entity):
        result_bullet = []
        for args in iter_:
            b = Bullet(*args, entity, is_add_queue=False)
            result_bullet.append(b)
        return result_bullet

    def _collision_rect(self, rect):
        res = rect.clipline(self.point_start, self.point_end)
        if res:
            print(res, self.rect.center, rect.center)
        return res

    def is_collision(self, *rect: pg.Rect) -> bool:
        for _ in range(int(max([j // k for j, k in zip(self.v, self.move_bullet)]))):
            rect_bullet = self.rect.move(*self.move_bullet)
            if rect_bullet.collidelist(rect) != -1:
                return rect[rect_bullet.collidelist(rect)]
        return False

    @classmethod
    def clear_queue(cls):
        res = tuple(cls.queue_bullet_mess)
        cls.queue_bullet_mess.clear()
        return res

    def __iter__(self):
        return iter((self.surface, self.rect))

    def __repr__(self):
        return ' '.join([str(round(i)) for i in self.pos_beg])
