import pygame

import os
import sys
import sqlite3
from random import randint, randrange
from math import sin, cos, radians, atan, sqrt, degrees


FPS = 60
clock = pygame.time.Clock()
BLACK = pygame.Color("black")
YELLOW = pygame.Color("yellow")
GREY = pygame.Color("grey")
RED = pygame.Color("red")
BLUE = pygame.Color("blue")
WHITE = pygame.Color("white")
GREEN = pygame.Color("green")
COOL_ORANGE = (250, 200, 60)
STRANGE_GREEN = (128, 147, 42)
CHARGE_BLUE = (135, 206, 250)

UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
# Изображения не получится загрузить
# без предварительной инициализации pygame
pygame.init()
info = pygame.display.Info()
screen_size = width, height = info.current_w, info.current_h
main_screen = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)

pygame.display.set_caption("Robot survivors")
target_size = 1000
border_first = 0
border_last = 2000


def load_image(name, colorkey=None):
    """Загружает указанное изображение, если может.
    Вырезает фон."""
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def mirror(image):
    """Отражает изображение по вертикали (вдоль оси x)"""
    return pygame.transform.flip(image, True, False)


def cut_sheet(sheet, columns, rows, mirror_line=-1):
    """Режет изображение на его составляющие"""
    frames = []
    rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                       sheet.get_height() // rows)
    for j in range(rows):
        temp = []
        for i in range(columns):
            frame_location = (rect.w * i, rect.h * j)
            temp.append(sheet.subsurface(pygame.Rect(
                frame_location, rect.size)))
        frames.append(temp)
        if j == mirror_line - 1:
            frames.append([mirror(image) for image in temp])
    return frames


def bleach(image):
    """Отбеливает изображение"""
    w, h = image.get_size()
    colorkey = image.get_colorkey()
    for x in range(w):
        for y in range(h):
            if image.get_at((x, y)) != colorkey:
                image.set_at((x, y), WHITE)
    return image


def greening(image):
    """Делает изображение зелёным"""
    w, h = image.get_size()
    colorkey = image.get_colorkey()
    for x in range(w):
        for y in range(h):
            if image.get_at((x, y)) != colorkey:
                image.set_at((x, y), GREEN)
    return image


def inside(x, y, rect):
    """Проверяет вхождение точки в прямоугольную область"""
    return (rect.x <= x <= rect.x + rect.w and
            rect.y <= y <= rect.y + rect.h)


def get_from_database(table, item_id):
    """Поиск элемента с id = item_id в таблице table
    базы данных items1.db. Возвращает список значений элемента."""
    database = sqlite3.connect(os.path.join('data', 'items1.db'))
    cursor = database.cursor()
    result = cursor.execute(f"""SELECT * FROM {table} WHERE 
    id = {item_id}""").fetchone()[1:]
    database.close()
    return result


# Группы спрайтов инициализируются здесь
all_sprites = pygame.sprite.Group()
interface = pygame.sprite.Group()
bars = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
character = pygame.sprite.GroupSingle()
background_group = pygame.sprite.GroupSingle()
items = pygame.sprite.Group()


# Ниже классы всего, с чем взаимодействует игрок
# <----------враги---------->
class Enemy(pygame.sprite.Sprite):
    # привязка спрайтов
    move_images = cut_sheet(load_image("bat.png", -1), 1, 1,
                            mirror_line=1)

    def __init__(self, groups=enemies):
        """Инициализация"""
        super().__init__(groups)

        # добавление в группу ко всем спрайтам
        self.add(all_sprites)

        # текущий спрайт
        self.counter = 0
        self.group = 0
        self.current_state = self.move_images
        self.current_image_group = self.current_state[self.group]
        self.image = self.current_image_group[self.counter]
        self.rect = self.image.get_rect()

        # основные параметры
        self.max_hp = 100
        self.current_hp = 100
        self.speed = 10
        self.exp = 0
        # урон тараном, если доступен
        self.damage = 2
        # позиция выбирается случайно,
        # где одна переменная равна нулю,
        # а другая случайному числу
        # в границах поля
        self.rect.x, self.rect.y = (
                                       randint(0, border_last),
                                       border_last * randint(0, 1)
                                   )[::1 - randint(0, 1) * 2]
        self.direction = 0

        self.weapon = None

    def check_for_target(self, x, y):
        """Проверка на то, возможно ли атаковать игрока"""
        if self.weapon is not None and \
           self.weapon.distance >= self.get_distance(x, y) and \
           self.weapon.reload == 0:
            return True
        return False

    def get_direction(self, x1, y1):
        """Вернёт угол от себя относительно
        точки с координатами (x, y)"""
        x2 = self.rect.x + self.rect.width // 2
        y2 = self.rect.y + self.rect.height // 2
        try:
            direction = degrees(atan((x1 - x2) / (y1 - y2))) + 90
            if y1 < y2:
                direction += 180
            return 180 - direction
        except ZeroDivisionError:
            if x1 < x2:
                return -180  # 180 - 360
            else:
                return 0  # 180 - 180

    def get_distance(self, x, y):
        """Вернёт расстояние от себя до точки с координатами (x, y)"""
        return sqrt((x - self.rect.x) ** 2 + (y - self.rect.y) ** 2)

    def move(self, direction):
        """Движение врага в направлении direction"""
        self.rect.x += self.speed * cos(radians(direction))
        self.rect.y += self.speed * sin(radians(direction))

    def get_damage(self, dmg):
        """Уменьшает здоровье врага на dmg"""
        self.current_hp -= dmg
        self.image = bleach(self.image.copy())

    def give_exp(self, mod):
        """Даёт опыт игроку при своей смерти, а также восстанавливает часть
        здоровья, если характеристика vampire игрока больше 0"""
        for char in character:
            char.current_exp += self.exp * mod
            char.current_hp += char.specifications['vampire']

    def death(self):
        """События смерти"""
        # можно добавить красивых эффектов
        self.give_exp(1)
        if self.weapon:
            self.weapon.kill()
        self.kill()

    def attack(self, direction, player_x, player_y):
        """Атакует точку, если может"""
        if self.weapon and \
                self.check_for_target(player_x, player_y):
            self.weapon.shoot(direction)

    def update(self):
        """Обновление спрайта"""
        # открывает доступ к игроку
        global player
        # извлекает его координаты
        player_x, player_y = player.get_position()
        # удаляет врага, если тот убит
        if self.current_hp <= 0:
            self.death()
        # получает угол до игрока
        self.direction = self.get_direction(player_x, player_y)
        # Не двигает, если цель есть в зоне поражения. Если оружия нет,
        # то игнорирует проверку.
        if not (self.weapon and self.get_distance(player_x, player_y) <=
                self.weapon.distance >> 1):
            # двигает по этому углу
            self.move(self.direction)
        # определение группы спрайтов на основе положения игрока
        if abs(self.direction) >= 90:
            self.group = 1  # вправо
        else:
            self.group = 0  # влево
        self.current_image_group = self.current_state[self.group]
        # счётчик смены спрайтов
        self.counter += 1
        # ограничение счётчика количеством спрайтов
        self.counter %= len(self.current_image_group) * 10
        # собственно, смена спрайта
        self.image = self.current_image_group[int(self.counter / 10)]

        self.attack(self.direction, player_x, player_y)


class Bat(Enemy):
    # привязка спрайтов
    move_images = cut_sheet(load_image("bat.png", -1), 4, 1,
                            mirror_line=1)

    def __init__(self, groups=enemies):
        """Инициализация"""
        super().__init__(groups)
        self.speed = 3
        self.max_hp = 8
        self.current_hp = self.max_hp

        self.exp = 50

    def attack(self, direction, player_x, player_y):
        """Производит эффект атаки (таранит собой)"""
        # проверяет столкновение с игроком
        collisions = pygame.sprite.spritecollide(
            self, character, False)
        # если да, то...
        if len(collisions) > 0:
            # наносит урон
            collisions[0].get_damage(self.damage)
            # получает урон, зависящий от
            # характеристики spikes персонажа
            self.current_hp -= collisions[0].specifications[
                                   'spikes'] / 10
            # увеличивает скорость для эффекта толчка
            self.speed = 35
            # отодвигается
            self.move((direction - 180) % 360)
            # возвращает скорость
            self.speed = 3


class Demon(Enemy):
    # привязка спрайтов
    move_images = cut_sheet(load_image("big_demon_walking.png", -1), 4,
                            1, mirror_line=1)
    idle_images = cut_sheet(load_image("big_demon_idle.png", -1), 4,
                            1, mirror_line=1)

    def __init__(self, groups=enemies):
        """Инициализация"""
        super().__init__(groups)
        self.speed = 2
        self.max_hp = 40
        self.current_hp = 40
        self.exp = 100
        self.weapon = Weapon(self)

    def update(self):
        """Обновление спрайта с учётом состояния"""
        super().update()
        # открывает доступ к игроку
        global player
        # проверяет, может ли оружие до него достать
        if (self.get_distance(*player.get_position()) <=
                self.weapon.distance >> 1):
            self.current_state = self.idle_images
        else:
            self.current_state = self.move_images


# <----------снаряды---------->
class Bullet(pygame.sprite.Sprite):
    """Определяется внутри класса weapon при вызове метода shoot"""

    def __init__(self, degree, position, speed=20, damage=4, limit=100,
                 pertain=0, radius=2, colour=YELLOW, groups=bullets):
        """Инициализация"""
        super().__init__(groups)
        self.add(all_sprites)

        # self.radius = radius
        # self.colour = colour

        # основные параметры
        self.degree = degree  # в градусах
        self.speed = speed
        self.distance = 0
        self.limit = limit
        self.damage = damage
        self.pertain = pertain
        # отрисовка
        self.image = pygame.Surface((2 * radius, 2 * radius),
                                    pygame.SRCALPHA, 32)
        pygame.draw.circle(self.image, colour,
                           (radius, radius), radius)
        self.rect = pygame.Rect(*position, 2 * radius, 2 * radius)

    def move(self):
        """Двигает снаряд"""
        # увеличивает пройденную дистанцию
        self.distance += self.speed
        # перемещает
        self.rect.x += self.speed * cos(radians(self.degree))
        self.rect.y += self.speed * sin(radians(self.degree))
        # проверяет лимит
        if self.distance >= self.limit:
            self.death()

    def death(self):
        """Удаление снаряда из игры"""
        # можно добавить красивых эффектов
        self.kill()

    def update(self):
        """Обновление спрайта"""
        self.move()
        collisions = pygame.sprite.spritecollide(
                self, (character, enemies)[self.pertain], False)
        if len(collisions) > 0:
            for sprite in collisions:
                sprite.get_damage(self.damage)
            self.death()


# <----------оружие---------->
class Weapon(pygame.sprite.Sprite):
    # привязка спрайтов оружия
    default_image = load_image("gun.png", -1)

    def __init__(self, owner, group=all_sprites):
        super().__init__(group)
        # носитель оружия
        self.owner = owner
        # текущий спрайт
        self.image = self.default_image
        self.rect = self.image.get_rect()
        self.bullet_size = 5
        self.bullet_colour = RED
        # смещение относительно владельца
        self.shift_y = (self.owner.rect.height - self.rect.h) * 0.6

        # основные параметры
        self.reload_time = 60
        self.diff = 0
        self.bullet_speed = 4
        self.bullet_pertain = 0
        self.distance = 500
        self.damage = 5
        self.mod = 1
        # текущее состояние
        self.reload = 0

    def shoot(self, direction):
        """Создаёт снаряд, летящий из указанной
        позиции под указанным углом, добавляет разброс"""
        x, y = self.rect.center
        x += 10 * cos(radians(direction))
        y += 10 * sin(radians(direction))

        diff = self.diff
        distance = self.distance
        damage = self.damage
        if isinstance(self.owner, Player):
            # бонусы характеристик игрока
            diff -= round(diff * (self.owner.specifications['accuracy'] / 100))
            distance += self.owner.specifications['range'] * 10
            damage += round(damage * (self.owner.specifications['%dmg'] /
                                      100)) + self.owner.specifications['+dmg']
        # разброс
        if diff != 0:
            direction += randrange(-diff, diff)
        # собственно, снаряд
        Bullet(direction, (x, y), self.bullet_speed,
               damage, distance, self.bullet_pertain,
               self.bullet_size, self.bullet_colour)
        # перезарядка
        if isinstance(self.owner, Player):
            self.reload = self.reload_time - round(self.reload_time * (
                    self.owner.specifications['attack speed'] / 100))
        else:
            self.reload = self.reload_time

    def update(self):
        """Обновление спрайта"""
        self.image = pygame.transform.rotate(self.default_image,
                                             180 - self.owner.direction)
        self.rect.x = self.owner.rect.x
        self.rect.y = self.owner.rect.y + self.shift_y
        self.reload -= 1 if self.reload > 0 else 0


# <----------само-оружие---------->
class RobotWeapon(Weapon):
    """Оружие робота"""
    default_image = mirror(load_image("robot_gun.png", -1))

    def __init__(self, owner, group=all_sprites):
        """Инициализация"""
        super().__init__(owner, group)

        self.reload_time = 20
        self.bullet_size = 5
        self.bullet_colour = COOL_ORANGE
        self.bullet_speed = 8
        self.distance = 400
        self.damage = 4
        self.bullet_pertain = 1


class CalculatorWeapon(Weapon):
    """Оружие калькулятора"""
    default_image = mirror(load_image("calculator_gun.png", -1))

    def __init__(self, owner, group=all_sprites):
        """Инициализация"""
        super().__init__(owner, group)

        self.reload_time = 24
        self.bullet_size = 7
        self.bullet_colour = COOL_ORANGE
        self.bullet_speed = 6
        self.distance = 400
        self.damage = 5
        self.bullet_pertain = 1


class CentipedeWeapon(Weapon):
    """Оружие гусеницы"""
    default_image = mirror(load_image("charge_blaster.png", -1))

    def __init__(self, owner, group=all_sprites):
        """Инициализация"""
        super().__init__(owner, group)

        self.reload_time = 4
        self.bullet_size = 5
        self.bullet_colour = CHARGE_BLUE
        self.bullet_speed = 12
        self.diff = 25
        self.distance = 550
        self.damage = 3
        self.bullet_pertain = 1


# <----------персонажи---------->
class Player(pygame.sprite.Sprite):
    """Самодостаточный класс персонажа игрока.
    Используется для наследования."""
    # привязка спрайтов
    idle_images = cut_sheet(load_image("robot_idle.png", -1), 4, 3,
                            mirror_line=2)
    move_images = cut_sheet(load_image("robot_walking.png", -1), 6, 3,
                            mirror_line=2)

    def __init__(self, groups=character):
        """Инициализация"""
        super().__init__(groups)
        self.add(all_sprites)

        # текущий спрайт
        self.animation_counter = 0
        self.group = 0
        self.current_image_group = self.idle_images[self.group]
        self.image = self.current_image_group[self.animation_counter]
        self.rect = self.image.get_rect()
        self.rect.y = self.rect.x = border_last >> 1

        # основные параметры
        self.pos_x = 0
        self.pos_y = 0
        self.specifications = {
            'health': 80,
            '%dmg': 0,
            '+dmg': 0,
            'dexterity': 0,
            'speed': 4,
            'vampire': 0,
            'regen': 0,
            'range': 0,
            'accuracy': 20,
            'armor': 0,
            'spikes': 0,
            'attack speed': 0
        }
        self.current_hp = 80
        self.direction = 0
        self.current_exp = 0
        self.exp_for_next_level = 1000
        # перемещение [up, down, left, right]
        self.actions = {"up": False, "down": False,
                        "left": False, "right": False, "shoot": False}
        self.regen_counter = 0

        self.weapon = None

    def get_direction(self, x1, y1):
        """Вернёт угол от себя относительно
        точки с координатами (x, y)"""
        x2 = self.rect.x + self.rect.width // 2
        y2 = self.rect.y + self.rect.height // 2
        try:
            direction = degrees(atan((x1 - x2) / (y1 - y2))) + 90
            if y1 < y2:
                direction += 180
            return 180 - direction
        except ZeroDivisionError:
            if x1 < x2:
                return -180  # 180 - 360
            else:
                return 0  # 180 - 180

    def set_direction(self, pos):
        """Устанавливает направление взгляда игрока"""
        if pos is not None:
            self.direction = self.get_direction(*pos)

        if 45 < self.direction < 135:
            self.group = 0  # вниз
        elif -45 <= self.direction <= 45:
            self.group = 1  # вправо
        elif not(-135 < self.direction < 135):
            self.group = 2  # влево
        elif -135 < self.direction < -45:
            self.group = 3  # вверх
        # если двигается, то...
        if any(tuple(self.actions.values())[:-1]):
            self.current_image_group = self.move_images[self.group]
        else:
            self.current_image_group = self.idle_images[self.group]

    def move(self):
        """Перемещает игрока"""
        # положение относительно земли (поля)
        self.pos_x = self.rect.x - all_sprites.sprites()[0].rect.x
        self.pos_y = self.rect.y - all_sprites.sprites()[0].rect.y
        # коэффициент для движения по диагонали
        coefficient = 1
        if sum(map(int, tuple(self.actions.values())[:-1])) > 1:
            coefficient = 0.84
        # установка величин в зависимости от направления
        x, y = 0, 0
        if self.actions['up']:
            y -= self.specifications['speed'] * coefficient
        if self.actions['down']:
            y += self.specifications['speed'] * coefficient
        if self.actions['left']:
            x -= self.specifications['speed'] * coefficient
        if self.actions['right']:
            x += self.specifications['speed'] * coefficient
        # проверка границ поля
        if not(border_first < self.pos_x + x < border_last -
               self.rect.width):
            x = 0
        if not(border_first < self.pos_y + y < border_last -
               self.rect.height):
            y = 0
        # собственно, сдвиг
        self.rect = self.rect.move(x, y)

    def set_action(self, index, value=True):
        """Устанавливает перемещение игрока"""
        self.actions[index] = value

    def shoot(self):
        """Атакует текущим оружием в направлении курсора"""
        if self.weapon.reload == 0:
            self.weapon.shoot(self.direction)
        else:
            pass  # звук/эффект невозможности совершения атаки

    def get_damage(self, dmg):
        """Уменьшает здоровье на dmg

        Также есть проверка на игнорирование атаки в случае,
        если характеристика dexterity персонажа больше 0"""
        if randint(0, 100) > self.specifications['dexterity']:
            dmg -= self.specifications['armor']
            if dmg < 1:
                dmg = 1
            self.current_hp -= dmg
            self.image = bleach(self.image.copy())
        else:
            self.image = greening(self.image.copy())

    def death(self):
        """События смерти персонажа"""
        # можно добавить красивых эффектов
        if self.weapon:
            self.weapon.kill()
        self.kill()

    def debug_view(self):
        """Функция отладки, показывает
        направление игрока к курсору и угол"""
        global main_screen
        font = pygame.font.Font(None, 20)
        text = [str(self.direction), f'{self.current_hp}/'
                                     f'{self.specifications["health"]}',
                f'on field:{self.pos_x}|{self.pos_y}',
                f'on screen:{self.rect.x}|{self.rect.x}']
        text_coord = 0
        for line in text:
            string_rendered = font.render(line, True,
                                          pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            text_coord += 8
            intro_rect.top = text_coord
            intro_rect.x = 2
            text_coord += intro_rect.height
            main_screen.blit(string_rendered, intro_rect)

        x = self.rect.x + self.rect.width // 2
        y = self.rect.y + self.rect.height // 2
        pygame.draw.line(main_screen, RED,
                         (x, y),
                         (x + 50 * cos(radians(self.direction)),
                          y + 50 * sin(radians(self.direction))))

    def get_position(self):
        """Возвращает центр персонажа"""
        return (self.rect.x + self.rect.width // 2,
                self.rect.y + self.rect.height // 2)

    def get_health(self):
        """Возвращает здоровье персонажа
        от максимальных значений в долях"""
        return self.current_hp / self.specifications['health']

    def get_experience(self):
        """Возвращает опыт персонажа
        от максимальных значений в долях"""
        return self.current_exp / self.exp_for_next_level

    def upgrade(self, item):
        """Изменяет характеристики персонажа на значения, соответствующие
        характеристикам предмета item, объекта класса Item"""
        # некоторые характеристики имеют лимит
        limits = {
            'dexterity': 90,
            'speed': 20,
            'accuracy': 100,
            'armor': 100,
            'attack speed': 80
        }
        for key in item.specifications.keys():
            self.specifications[key] += item.specifications[key]
            if key in limits and self.specifications[key] > limits[key]:
                self.specifications[key] = limits[key]
            elif self.specifications[key] < 0:
                if key == 'health':
                    self.specifications[key] = 1
                else:
                    self.specifications[key] = 0

    def update(self):
        """Обновление спрайта"""
        # self.debug_view()
        # движение
        self.move()
        # атака
        if self.actions["shoot"]:
            self.shoot()
        # обзор (на случай бездействия курсора)
        self.set_direction(None)
        # счётчик смены спрайтов
        self.animation_counter += 1
        # ограничение счётчика количеством спрайтов
        self.animation_counter %= len(self.current_image_group) * 10
        # собственно, смена спрайта
        self.image = self.current_image_group[
            int(self.animation_counter / 10)]
        # проверка на повышение уровня
        if self.current_exp >= self.exp_for_next_level:
            self.current_exp -= self.exp_for_next_level
            self.exp_for_next_level *= 1.4
            # должно будет вызываться меню апгрейда
        # восстановление здоровья раз в некоторое время
        if self.specifications['regen'] > 0:
            self.regen_counter += 1
            if self.regen_counter == 900:
                self.regen_counter = 0
                self.current_hp += self.specifications['regen']
        # если здоровье больше максимума,
        # снижает его до допустимого значения
        if self.current_hp > self.specifications['health']:
            self.current_hp = self.specifications['health']


# <----------сами-персонажи---------->
options = ("Robot", "Calculator", "Centipede")


class Robot(Player):
    """Персонаж робота"""
    # привязка спрайтов
    idle_images = cut_sheet(load_image("robot_idle.png", -1), 4, 3,
                            mirror_line=2)
    move_images = cut_sheet(load_image("robot_walking.png", -1), 6, 3,
                            mirror_line=2)

    def __init__(self, groups=character):
        super().__init__(groups)
        self.specifications = {
            'health': 80,
            '%dmg': 0,
            '+dmg': 0,
            'dexterity': 0,
            'speed': 5,
            'vampire': 0,
            'regen': 0,
            'range': 0,
            'accuracy': 0,
            'armor': 0,
            'spikes': 0,
            'attack speed': 0
        }
        self.weapon = RobotWeapon(self)


class Calculator(Player):
    """Персонаж калькулятора"""
    # привязка спрайтов
    idle_images = cut_sheet(load_image("calculator_idle.png", -1), 4, 3,
                            mirror_line=2)
    move_images = cut_sheet(load_image("calculator_walking.png", -1), 6,
                            3, mirror_line=2)

    def __init__(self, groups=character):
        super().__init__(groups)
        self.specifications = {
            'health': 100,
            '%dmg': 0,
            '+dmg': 0,
            'dexterity': 0,
            'speed': 4,
            'vampire': 0,
            'regen': 0,
            'range': 0,
            'accuracy': 0,
            'armor': 0,
            'spikes': 0,
            'attack speed': 0
        }
        self.current_hp = 100
        self.weapon = CalculatorWeapon(self)


class Centipede(Player):
    """Персонаж гусеницы"""
    idle_images = cut_sheet(load_image("centipede_idle.png", -1), 1,
                            3, mirror_line=2)
    move_images = cut_sheet(load_image("centipede_walking.png", -1), 6,
                            3, mirror_line=2)

    def __init__(self, groups=character):
        super().__init__(groups)
        self.specifications = {
            'health': 500,
            '%dmg': 0,
            '+dmg': 0,
            'dexterity': 0,
            'speed': 2,
            'vampire': 0,
            'regen': 0,
            'range': 0,
            'accuracy': 0,
            'armor': 0,
            'spikes': 0,
            'attack speed': 0
        }
        self.current_hp = 500
        self.weapon = CentipedeWeapon(self)


# <----------предметы---------->
class Item(pygame.sprite.Sprite):
    def __init__(self, name, specifications, image, cost, groups=items):
        super().__init__(groups)
        self.name = name
        self.cost = cost
        self.image = load_image(image, -1)
        self.rect = self.image.get_rect()
        self.specifications = {}
        self.description = str()
        specifications_names = {'hp': ('health', 'Здоровье'),
                                '%d': ('%dmg', 'Бонусный % урона оружия'),
                                '+d': ('+dmg', 'Бонусный урон оружия'),
                                'dx': ('dexterity', 'Ловкость'),
                                'sp': ('speed', 'Скорость'),
                                'vp': ('vampire', 'Вампиризм'),
                                'rg': ('regen', 'Регенерация'),
                                'rn': ('range', 'Бонусная дальность оружия'),
                                'ac': ('accuracy', 'Меткость'),
                                'ar': ('armor', 'Броня'),
                                'sk': ('spikes', 'Шипы'),
                                'as': ('attack speed', 'Бонусный % скорости '
                                                       'атаки')}
        for elem in specifications.split('_'):
            self.specifications[specifications_names[elem[:2]][0]] = \
                int(elem[2:])
            if int(elem[2:]) > 0:
                sign = '+'
            else:
                sign = ''
            self.description += f'\n{specifications_names[elem[:2]][1]} ' \
                                f'{sign}{elem[2:]}'
        self.description = self.description[1:]


# <----------интерфейс---------->
class Camera:
    """Сдвигает спрайты так, чтобы выбранный объект оказался в центре"""
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        """Сдвинуть объект obj на смещение камеры"""
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        """Позиционировать камеру на объекте target"""
        self.dx = -(target.rect.x + target.rect.w // 2 - width // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - height // 2)


class Button(pygame.sprite.Sprite):
    """Кнопка интерфейса"""
    images = cut_sheet(load_image("button.png", -1), 2, 2)

    def __init__(self, position, text, groups=interface):
        """Инициализация кнопки, отрисовка текста на ней."""
        super().__init__(groups)
        self.state = self.images[0]
        self.image = self.state[0].copy()
        self.rect = self.image.get_rect()
        self.shift = 2
        # инициализация шрифта
        font = pygame.font.SysFont("ComicSans", 28 - len(text))
        self.string_text = text
        self.text = font.render(text, True, WHITE)

        self.rect.x, self.rect.y = position

    def hold(self, pos):
        """Нажимает на кнопку. Возвращает истину,
        если нажата успешно."""
        if inside(*pos, self.rect):
            self.state = self.images[1]
            self.shift = 0
            return True
        return False

    def release(self, pos):
        """Отпускает кнопку. Возвращает истину,
        если нажатие завершено верно."""
        if inside(*pos, self.rect):
            self.state = self.images[0]
            # если эта кнопка была нажата
            if self.shift == 0:
                self.shift = 2
                return True
        else:
            self.state = self.images[0]
        self.shift = 2
        return False

    def get_text(self):
        """Возвращает свой текст"""
        return self.string_text

    def update(self, pos):
        """Обновление состояния"""
        # если наведён курсор, то выделится
        if inside(*pos, self.rect):
            self.image = self.state[1].copy()
        else:
            self.image = self.state[0].copy()
        self.image.blit(self.text, (
            (self.rect.w - self.text.get_width()) // 2 - self.shift,
            (self.rect.h - self.text.get_height()) // 2 - self.shift
        ))


class Picture(pygame.sprite.Sprite):
    """Позволяет установить и нарисовать картинку."""
    def __init__(self, image, groups=interface):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect()

    def set_position(self, x, y):
        self.rect = self.rect.move(x, y)

    def set_picture(self, image):
        self.image = image


class Borders:
    """Класс бортиков, ограничивающих экран так,
    чтобы остался указанный квадрат."""
    def __init__(self, t_s=1000):
        """Инициализация"""
        # ширина горизонтальных линий
        hw = (height - t_s) >> 1
        # расстояние от края экрана для горизонтальных линий
        hp = (hw >> 1) - 1
        # ширина вертикальных линий
        vw = (width - t_s) >> 1
        # расстояние от края экрана для вертикальных линий
        vp = (vw >> 1) - 1
        # сохранение параметров бортиков, чтобы не просчитывать
        # их каждый раз при рисовании
        self.params = (
            ((0, hp), (width, hp), hw),
            ((0, height - hp), (width, height - hp), hw),
            ((vp, 0), (vp, height), vw),
            ((width - vp, 0), (width - vp, height), vw),
        )

    def draw(self, screen):
        """Отрисовка"""
        for parameter in self.params:
            pygame.draw.line(screen, BLACK, *parameter)


class Bar(pygame.sprite.Sprite):
    """Класс шкалы для отображения параметров."""
    def __init__(self, rect, color, groups=bars):
        """Инициализация"""
        super().__init__(groups)
        self.image = pygame.Surface((rect.w, rect.h),
                                    pygame.SRCALPHA, 32)
        pygame.draw.rect(self.image, WHITE, (0, 0, rect.w, rect.h), 1)
        self.rect = rect
        self.fraction = 1.
        self.color = color
        self.update()

    def set_fraction(self, fraction):
        """Установка степени заполненности"""
        # если значение изменилось
        if fraction != self.fraction:
            # перевод из процентов в доли
            self.fraction = min(fraction, 1.)
            self.update()

    def update(self):
        # очистка шкалы
        pygame.draw.rect(self.image, BLACK,
                         (1, 1, self.rect.w - 2, self.rect.h - 2), 0)
        # заполнение
        pygame.draw.rect(self.image, self.color,
                         (1, 1, int((self.rect.w - 2) * self.fraction),
                          self.rect.h - 2), 0)


def text_object(string, pos_x=0, pos_y=0, size=40, color=BLACK):
    font = pygame.font.SysFont("ComicSans", size)
    string_rendered = font.render(string, True, color)
    text_position = string_rendered.get_rect()
    text_position.x = pos_x
    text_position.y = pos_y
    return string_rendered, text_position


# <-----функции-основного-процесса----->
def menu(screen):
    """Меню со своим циклом. Пока открыто,
    игра приостановлена."""
    global clock
    running = True
    # инициализация кнопок
    middle = width // 2 - 75
    start = int(height * 0.4)
    text = ("Продолжить", "Выйти из игры")
    buttons = []
    for string in text:
        buttons.append(Button((middle, start), string))
        start += 50
    # текст
    screen_name = text_object("Пауза", width // 2 - 75, height // 3)
    while running:
        for event in pygame.event.get():
            # закрытие приложения
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # нажатие клавиш мыши
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.hold(event.pos):
                        break
            # отпускание клавиш мыши
            if event.type == pygame.MOUSEBUTTONUP:
                for button in buttons:
                    if button.release(event.pos):
                        if button.get_text() == "Продолжить":
                            running = False
                        if button.get_text() == "Выйти из игры":
                            pygame.quit()
                            sys.exit()
            # нажатие клавиш клавиатуры
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        screen.fill(STRANGE_GREEN)
        interface.draw(screen)
        interface.update(pygame.mouse.get_pos())

        screen.blit(*screen_name)

        clock.tick(FPS)
        pygame.display.flip()
    # очистка кнопок
    for element in interface:
        element.kill()


def start_screen(screen):
    """Начальный экран со своим циклом.
    Возвращает выбранного персонажа."""
    global clock, options
    running = True
    # текст
    screen_name = text_object(
        "Robot survivors", width // 3, height // 4, 60)
    # инициализация кнопок
    middle = int(height * 0.6)
    start = int(width * 0.3)
    text = ("Выйти из игры", "Настройки", "<", "Начать", ">")
    buttons = []
    for string in text:
        buttons.append(Button((start, middle), string))
        start += 130

    # варианты персонажей
    preview = cut_sheet(load_image("preview.png", -1),
                        len(options), 1)[0]
    choice = 0
    image = Picture(preview[choice])
    # картинка персонажа
    image.set_position(start - 225, middle - 100)
    while running:
        for event in pygame.event.get():
            # закрытие окна
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # нажатие клавиш мыши
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.hold(event.pos):
                        break
            # отпускание клавиш мыши
            if event.type == pygame.MOUSEBUTTONUP:
                for button in buttons:
                    if button.release(event.pos):
                        if button.get_text() in "<>":
                            if button.get_text() == '<':
                                choice -= 1
                            elif button.get_text() == '>':
                                choice += 1
                            choice %= len(options)
                            image.set_picture(preview[choice])
                        if button.get_text() == "Начать":
                            # очистка кнопок
                            for element in interface:
                                element.kill()
                            return choice
                        if button.get_text() == "Выйти из игры":
                            pygame.quit()
                            sys.exit()
                        if button.get_text() == "Настройки":
                            for element in interface:
                                element.kill()
                            return -1

        screen.fill(STRANGE_GREEN)
        interface.draw(screen)
        interface.update(pygame.mouse.get_pos())

        interface.draw(screen)
        screen.blit(*screen_name)

        clock.tick(FPS)
        pygame.display.flip()


def end_screen(screen, survived_time=-1):
    global clock
    """Экран конца игры, принимает прожитое время для экрана
    смерти, в противном случае поздравляет с победой."""
    if survived_time == -1:
        fill_color = WHITE
        ending_image = load_image("greetings.png")
    else:
        fill_color = BLACK
        ending_image = load_image("dead.png")
        ending_image.blit(*text_object(
            f"Вам удалось продержаться " +
            f"{survived_time // 60}:{survived_time % 60}",
            150, 250, 40, BLACK))
    ending_image = pygame.transform.scale(ending_image, (width, height))
    size = width // 10
    for i in range(11):
        pygame.draw.line(screen, fill_color, (i * size, 0),
                         (i * size, height), size)
        clock.tick(20)
        pygame.display.flip()
    for i in range(11):
        screen.blit(ending_image, (i * size - width, 0))
        clock.tick(20)
        pygame.display.flip()
    running = True
    buttons = [Button((width // 2, int(height * 0.6)), "Выйти из игры")]
    while running:
        for event in pygame.event.get():
            # закрытие окна
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # нажатие клавиш мыши
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.hold(event.pos):
                        break
            # отпускание клавиш мыши
            if event.type == pygame.MOUSEBUTTONUP:
                for button in buttons:
                    if button.release(event.pos):
                        if button.get_text() == "Выйти из игры":
                            pygame.quit()
                            sys.exit()
        screen.blit(ending_image, (0, 0))

        interface.draw(screen)
        interface.update(pygame.mouse.get_pos())

        clock.tick(FPS)
        pygame.display.flip()
    pygame.quit()


def settings(screen):
    """Настройки некоторых параметров игры."""
    # кнопки
    middle = int(width * 0.1)
    start = int(height * 0.3)
    text = ("Вверх", "Вниз", "Влево", "Вправо",
            "Сохранить", "Сбросить", "Выйти")
    buttons = []
    for string in text:
        buttons.append(Button((middle, start), string))
        start += 50
    # название экрана
    screen_name = text_object(
        "Robot survivors", width // 3, height // 4, 60)
    running = True
    while running:
        for event in pygame.event.get():
            # закрытие окна
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # нажатие клавиш мыши
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.hold(event.pos):
                        break
            # отпускание клавиш мыши
            if event.type == pygame.MOUSEBUTTONUP:
                for button in buttons:
                    if button.release(event.pos):
                        if button.get_text() == "Выйти":
                            for element in buttons:
                                element.kill()
                            running = False
                        elif button.get_text() == "Вверх":
                            pass
        screen.fill(STRANGE_GREEN)

        interface.draw(screen)
        interface.update(pygame.mouse.get_pos())

        interface.draw(screen)
        screen.blit(*screen_name)

        clock.tick(FPS)
        pygame.display.flip()


def upgrade_menu(screen):
    # пример создания предмета
    cost = randint(250, 500)
    Item(*(get_from_database('items1', 1) + [cost]))


def main():
    """Основной цикл игры со своими инициализаторами"""
    global main_screen, player, clock
    index = -1
    # пока не нажата кнопка "начать", игрок перемещается между экранами
    while index == -1:
        index = start_screen(main_screen)
        if index == -1:
            settings(main_screen)
    running = True
    # инициализация камеры
    camera = Camera()
    # инициализация бортиков
    borders = Borders(target_size)
    # земля
    ground = pygame.sprite.Sprite()
    ground.image = pygame.transform.scale(load_image('ground2.png', -1),
                                          [border_last] * 2)
    ground.rect = ground.image.get_rect()
    all_sprites.add(ground)
    # фон
    # единственный спрайт, которого нет в all_sprites
    background = pygame.sprite.Sprite()
    background.image = pygame.transform.scale(
        load_image('full_back.png'), screen_size)
    background.rect = background.image.get_rect()
    background_group.add(background)

    # инициализация персонажа
    player = eval(options[index] + "()")
    # полоски здоровья и опыта
    health_text = text_object("Здоровье", 320, 1030, 30, WHITE)
    health_bar = Bar(pygame.rect.Rect(460, 1050, target_size, 15),
                     RED)
    experience_text = text_object("Опыт", 360, 0, 30, WHITE)
    experience_bar = Bar(pygame.rect.Rect(460, 20, target_size, 15),
                         BLUE)
    # таймер общего времени
    timer_event_type = pygame.USEREVENT + 1
    # раз в секунду
    pygame.time.set_timer(timer_event_type, 1000)
    # счётчик времени
    seconds_counter = 0
    # текст отображения времени
    time_text = text_object("Время", 10, 0, 40, WHITE)
    time_counter = text_object(
        f"{seconds_counter // 60}:{seconds_counter % 60}",
        10, 50, 40, WHITE)
    while running:
        for event in pygame.event.get():
            # закрытие окна
            if event.type == pygame.QUIT:
                running = False
            # нажатие клавиш клавиатуры
            if event.type == pygame.KEYDOWN:
                # направление движения персонажа
                if event.key in UP_KEYS:
                    player.set_action("up")
                elif event.key in DOWN_KEYS:
                    player.set_action("down")
                if event.key in RIGHT_KEYS:
                    player.set_action("right")
                elif event.key in LEFT_KEYS:
                    player.set_action("left")

                if event.key == pygame.K_ESCAPE:
                    # пауза/меню
                    menu(main_screen)
            # отпускание клавиш клавиатуры
            if event.type == pygame.KEYUP:
                # прекращение движения персонажа
                if event.key in UP_KEYS:
                    player.set_action("up", False)
                elif event.key in DOWN_KEYS:
                    player.set_action("down", False)
                if event.key in RIGHT_KEYS:
                    player.set_action("right", False)
                elif event.key in LEFT_KEYS:
                    player.set_action("left", False)
            # движение мыши
            if event.type == pygame.MOUSEMOTION:
                # устанавливаем обзор на курсор
                player.set_direction(event.pos)
            # нажатие клавиш мыши
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    player.set_action("shoot", True)
            # отпускание клавиш мыши
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    player.set_action("shoot", False)
            # событие таймера (происходит раз в секунду)
            if event.type == timer_event_type:
                # появление врагов
                if seconds_counter % 8 == 0:
                    for i in range(randint(4, 7)):
                        Bat()
                    for i in range(randint(1, 3)):
                        Demon()
                # счёт секунд
                seconds_counter += 1
                # текст отображения времени
                time_counter = text_object(
                    f"{seconds_counter // 60}:{seconds_counter % 60}",
                    10, 50, 40, WHITE)

        background_group.draw(main_screen)

        # изменяем ракурс камеры
        camera.update(player)
        # обновляем положение всех спрайтов
        for sprite in all_sprites:
            camera.apply(sprite)
        # обновление всего
        all_sprites.draw(main_screen)
        all_sprites.update()
        # бортики
        borders.draw(main_screen)
        # интерфейс на бортиках
        main_screen.blit(*health_text)
        health_bar.set_fraction(player.get_health())
        main_screen.blit(*experience_text)
        experience_bar.set_fraction(player.get_experience())
        bars.draw(main_screen)
        main_screen.blit(*time_counter)
        main_screen.blit(*time_text)

        clock.tick(FPS)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
