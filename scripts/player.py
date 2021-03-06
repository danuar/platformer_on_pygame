import time
from typing import List, Tuple, Union
from .basic import BasicClass, GameObject
from random import choice
from .chat import get_config_value, set_config_value
from .weapon import Weapon, Gun
from .singleton import BaseVector, Camera

import pygame as pg


class Player(BasicClass):
    """Класс для создания и управления главным героем"""
    font: pg.font.Font = None

    def __init__(self, Surface: pg.Surface, size: Tuple[int, int] = None, start_frame_anim=0, stop=None,
                 k_arm=(6, 1.5), speed_animation: int = 0, default_spawn: Tuple[int, int] = (0, 0),
                 speed_animation_death: int = 5, entity=(), is_centering_camera=True, name=None):
        super().__init__()
        self.name = get_config_value('settings', 'name')
        if name is not None:
            self.name = name
        else:
            self.name = get_config_value('settings', 'name')
        if self.name == 'None' or len(self.name) > 10:
            self.name = f'Player{"".join([choice("1234567890") for _ in range(4)])}'
            set_config_value('settings', 'name', self.name)
        self.gen = self.death_image = None
        self.last_time_anim = time.time()
        self.last_time = time.perf_counter()
        self.is_damage = False
        self.weapon_now = 0
        self.interface_list = []
        self.last_num_weapon = 11
        self.entity = list(entity)
        self.lock = False
        self.anim = (start_frame_anim, stop)
        self.default_spawn = default_spawn
        self.speed_anim = speed_animation
        self.speed_animation_death = speed_animation_death
        self.surface = Surface
        self.size = size
        self.k = k_arm

        self._set_default_value()
        self.arm = (0, 0)
        self.list_image = []
        self.rect = pg.rect.Rect(0, 0, 0, 0)
        self.is_move_camera = True
        if is_centering_camera:
            self.is_move_camera = 'player'
        self.frame_image = pg.Surface((1, 1))

    def load_animation(self, name: str, color: Tuple[int, int, int] = None, path='resources/', name_image='f',
                       expansion='.png', _def_color=(255, 0, 0), distance=0):
        """Указываем путь к папке, где находяться изображения героя, и указываем её имя"""
        super(Player, self).load_animation(name, color, path, name_image, expansion, _def_color, distance)

        self.rect: pg.rect.Rect = self.list_image[0].get_rect(bottomleft=self.default_spawn)
        self.gen = self._generator_animation()
        self.animation()

    def add_element_interface(self, panel: pg.Surface, frame: pg.Surface):
        self.panel = GameObject(panel, BaseVector(0, 0) * (.5, .93))
        self.panel_frame = frame
        h = panel.get_size()[0]
        p = frame.get_size()[0]
        m = h - p*9
        r = (m//10, (m - m//10)//8)
        self.slice = [r[1], h+1, p+r[0]]

    def update_element_interface(self):
        self.panel.update(BaseVector(0, 0) * (.5, .93))

    def _set_default_value(self):
        self.is_dir = self.is_flip = self.stop_anim = self.is_death = False
        self.diff_time = 1
        self.event_list = []
        self.inventory: List[Union[Weapon, Gun]] = [None] * 9
        self.health = 100
        self.is_jump = -1
        self.speed = 4.5

    def _generator_animation(self):
        while True:
            for i in self.list_image[self.anim[0]:self.anim[1]]:
                yield self.frame_image if self.stop_anim else i
    
    def _generator_animation_death(self):
        sp = self.speed_anim
        self.speed_anim = 0
        self.frame_image = self.list_image[self.anim[0]]
        surface_copy = self.frame_image.copy()
        size = self.frame_image.get_size()

        for i in self.inventory:  # Очистка инвенторя
            if i is not None:
                i.is_up = False

        for i in range(240, -1, -self.speed_animation_death):  # Исчезновение игрока

            pix_array = pg.PixelArray(self.frame_image)
            for j in range(size[0]):
                for k in range(size[1]):
                    map_pixel = self.frame_image.unmap_rgb(pix_array[j, k])
                    if map_pixel[3] != 0:
                        pix_array[j, k] = (*map_pixel[:-1], i)
            surface = pix_array.make_surface()
            pix_array.close()
            yield surface

        self.list_image[self.anim[0]] = surface_copy

        while time.time() - self.time_death < 5:
            if self.is_move_camera != 'player': break
            text = self.font.render(f'Возрождение через: {int(5 - (time.time() - self.time_death))}', 1, (33, 33, 33))
            rect = text.get_rect(center=BaseVector(0, 0)*(.5, .5))
            self.surface.blit(text, rect)
            yield surface
        self.speed_anim = sp
        yield self.revival()

    def revival(self) -> pg.Surface:
        self._set_default_value()
        self.rect = self.frame_image.get_rect(bottomleft=self.default_spawn)
        self.gen = self._generator_animation()
        self.lock = False
        return self._flip(next(self.gen))

    def animation(self) -> pg.Surface:
        if time.time() - self.last_time_anim >= self.speed_anim:
            self.frame_image = self._flip(next(self.gen))
            self.last_time_anim = time.time()
        return self.frame_image

    def is_let(self, group_let: List[pg.rect.Rect] = None) -> bool:
        if group_let is None:
            group_let = self.group_let
        if self.rect.collidelist(group_let) != -1:
            return True
        return False

    def control(self, button: pg.event.Event):
        for i in [pg.K_w, pg.K_a, pg.K_s, pg.K_d, pg.K_SPACE]:
            if button.key == i:
                self.event_list.append(i)

    def set_pose(self, num_pos=0):
        self.frame_image = self._flip(self.list_image[num_pos])

    def _flip(self, image):
        if self.lock: return self.frame_image
        return pg.transform.flip(image, 1, 0) if self.is_flip else image

    def _switch_jump(self):
        self.is_jump = 27

    def _update_attr(self):
        # Поворот игрока
        if (not self.is_flip) and pg.K_a in self.event_list:
            self.is_flip = True
        if self.is_flip and pg.K_d in self.event_list:
            self.is_flip = False
    
    def death(self):
        if self.health <= 0:
            self.time_death = time.time()
            self.health = 100
            self.is_death = self.lock = True
            self.gen = self._generator_animation_death()

    def move(self, x, y) -> int:
        """Return index Let crossed with player"""
        if self.lock: return
        r = super(Player, self).move(x, y)
        self.update_pos_arm()
        return r

    def update_pos_arm(self):
        # Обновляем координаты руки
        w, h = self.rect.width, self.rect.height
        pos = w - w // self.k[0], h // self.k[1]
        self.arm = self.rect.left + pos[0], self.rect.top + pos[1]

    def __call__(self):
        self.diff_time = (time.perf_counter() - self.last_time) * 60
        self.last_time = time.perf_counter()
        if self.diff_time > 4:
            self.diff_time = 4

        # Смерть на низкой высоте
        if self.rect.y > 10000:
            self.health -= 2
            if self.health <= 0:
                self.rect = self.frame_image.get_rect(topleft=(300, 0))

        sp = self.speed  # Копия скорости
        G = 9.8
        self._update_attr()

        for el in self.event_list:
            num = {el == pg.K_w: lambda: self.move(0, -self.speed),
                   el == pg.K_a: lambda: self.move(-self.speed, 0),
                   el == pg.K_s: lambda: self.move(0, self.speed),
                   el == pg.K_d: lambda: self.move(self.speed, 0),
                   el == pg.K_SPACE and self.is_jump == 0: self._switch_jump
                   }.get(True, lambda: 0)()
        if self.is_jump != 0:
            self.set_pose(1)
        elif len(self.event_list) == 0:
            self.set_pose()

        num = self.move(0, G - self.is_jump)
        if self.get_weapon_now() is not None:
            self.get_weapon_now().update_weapon()
        if self.is_jump < 0 and self.is_dir:  # Обнуление ускорения если игрок на земле
            self.is_jump = 0
        if num != -1:  # Если внизу есть препятствие
            self.is_dir = True
        elif num == -1:  # Если под игроком нет препятствий, то он не на земле
            self.is_dir = False
            if self.is_jump == 0:
                self.is_jump = 0.1
        if self.is_jump != 0 and self.is_jump > -70:
            k = G // 6
            self.is_jump -= k if self.is_jump - k != 0 else -0.999
        self.speed = sp  # Возврат изначального значения скорости
        self.death()

    def draw_interface(self):
        if not self.is_death:
            self.fill_line(self.surface, *self.pos_over(10), self.health, (0, 255, 0))  # Полоска здоровья
        weapon = self.get_weapon_now()
        if weapon is not None and weapon.is_reload:
            level = (time.time() - weapon.last_time_reload) / weapon.time_reload * 100
            self.fill_line(self.surface, *self.pos_over(15), level, (255, 255, 255))
        if self.is_move_camera is True:
            return
        for game_obj in self.interface_list:
            self.surface.blit(*game_obj)
        if self.weapon_now == self.last_num_weapon:
            self.surface.blit(self.panel.last_frame, self.panel.rect)
            return
        panel = self.panel.frame_image.copy()
        for count, i in enumerate(range(*self.slice)):
            if count > 8:
                break
            elif count == self.weapon_now:
                sur = pg.Surface((self.panel_frame.get_size()[0], 1000))
                sur.fill((80, 80, 80))
                panel.blit(sur, (i, -8))
            if self.inventory[count] is not None:
                if self.inventory[count].icon is None:
                    self.inventory[count].icon = pg.transform.scale(self.inventory[count].image,
                                                                    [j - 10 for j in self.panel_frame.get_size()])
                panel.blit(self.inventory[count].icon, (i+4, 13))
            panel.blit(self.panel_frame, (i, 8))
        self.surface.blit(panel, self.panel.rect)
        self.panel.last_frame = panel
        self.last_num_weapon = self.weapon_now

    def draw_let(self):
        rect_camera = Camera.get_rect_camera()
        for let in self.group_let:
            if rect_camera.colliderect(let.rect):
                Camera.draw_obj(self.surface, *let)

    def get_weapon_now(self, is_name=False):
        result = self.inventory[self.weapon_now]
        return result.name if is_name and result else result

    def pos_over(self, value: int):
        return (self.rect.left, self.rect.top-value), (self.rect.right, self.rect.top-value)

    def __repr__(self):
        return f'<Player: {self.name}, center={self.rect.center}, jump={self.is_jump}, event={self.event_list}, ' \
               f'entity={", ".join([pl.name for pl in self.entity])}, diff_time={round(self.diff_time, 2)}, arm={self.arm}>'
