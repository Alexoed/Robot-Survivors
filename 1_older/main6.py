import pygame

import os
import sys
from random import randint
from math import sin, cos, radians, atan, sqrt, degrees


FPS = 60
clock = pygame.time.Clock()
BLACK = pygame.Color('black')
YELLOW = pygame.Color('yellow')
GREY = pygame.Color('grey')
RED = pygame.Color('red')
COOL_ORANGE = (247, 148, 60)
STRANGE_GREEN = (128, 147, 42)
WHITE = (255, 255, 255)

UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
# Изображения не получится загрузить
# без предварительной инициализации pygame
pygame.init()
screen_size = width, height = 800, 800
main_screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Robot survivors")
border_first = 0
border_last = 2000


def load_image(name, colorkey=None):
    """Загружает указанное изображение, если может. Вырезает фон."""
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
    """Отражает изображение по горизонтали"""
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


def inside(x, y, rect):
    """Проверяет вхождение точки в прямоугольную область"""
    return (rect.x <= x <= rect.x + rect.w and
            rect.y <= y <= rect.y + rect.h)


# Группы спрайтов инициализируются здесь
all_sprites = pygame.sprite.Group()
buttons = pygame.sprite.Group()
pictures = pygame.sprite.GroupSingle()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
character = pygame.sprite.GroupSingle()
background_group = pygame.sprite.GroupSingle()


# Ниже классы всего, с чем взаимодействует игрок
# <----------враги---------->
class Enemy(pygame.sprite.Sprite):
    # привязка спрайтов
    move_images = cut_sheet(load_image("bat.png", -1), 1, 1,
                            mirror_line=1)

    def __init__(self, groups=enemies):
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
                                       randint(0, border_last), 0
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

    def give_exp(self, mod):
        """Даёт опыт игроку при своей смерти"""
        for char in character:
            char.exp += self.exp * mod

    def death(self):
        """События смерти врага"""
        # можно добавить красивых эффектов
        if self.weapon:
            self.weapon.kill()
        self.kill()

    def attack(self, direction, player_x, player_y):
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
            # увеличивает скорость для эффекта толчка
            self.speed = 30
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
        super().__init__(groups)
        # добавление в группу, соответствующую тому, кому принадлежит
        # выпущенный снаряд: игроку или врагу
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
        self.shift_y = self.owner.rect.height * 0.55

        # основные параметры
        self.reload_time = 60
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
        # собственно, снаряд
        Bullet(direction, (x, y), self.bullet_speed,
               self.damage, self.distance, self.bullet_pertain,
               self.bullet_size, self.bullet_colour)
        # перезарядка
        self.reload = self.reload_time

    def update(self):
        self.image = pygame.transform.rotate(self.default_image,
                                             180 - self.owner.direction)
        self.rect.x = self.owner.rect.x
        self.rect.y = self.owner.rect.y + self.shift_y
        self.reload -= 1 if self.reload > 0 else 0


class RobotWeapon(Weapon):
    default_image = mirror(load_image("Robot_gun.png", -1))

    def __init__(self, owner, group=all_sprites):
        super().__init__(owner, group)

        self.reload_time = 20
        self.bullet_size = 5
        self.bullet_colour = COOL_ORANGE
        self.bullet_speed = 6
        self.distance = 400
        self.damage = 4
        self.bullet_pertain = 1


# <----------персонажи---------->
options = ("Robot", "Calculator")


class Player(pygame.sprite.Sprite):
    """Самодостаточный класс персонажа игрока.
    Используется для наследования."""
    # привязка спрайтов
    idle_images = cut_sheet(load_image("robot_idle.png", -1), 4, 3,
                            mirror_line=2)
    move_images = cut_sheet(load_image("robot_walking.png", -1), 6, 3,
                            mirror_line=2)

    def __init__(self, groups=character):
        super().__init__(groups)
        self.add(all_sprites)

        # текущий спрайт
        self.counter = 0
        self.group = 0
        self.current_image_group = self.idle_images[self.group]
        self.image = self.current_image_group[self.counter]
        self.rect = self.image.get_rect()

        # основные параметры
        self.pos_x = 0
        self.pos_y = 0
        self.max_hp = 100
        self.current_hp = 100
        self.speed = 4
        self.direction = 0
        self.exp = 0
        self.exp_for_next_level = 100
        # перемещение [up, down, left, right]
        self.actions = {"up": False, "down": False,
                        "left": False, "right": False, "shoot": False}

        self.weapon = RobotWeapon(self)

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
        if sum(map(int, self.actions.values())) > 1:
            coefficient = 0.85
        # установка величин в зависимости от направления
        x, y = 0, 0
        if self.actions['up']:
            y -= self.speed * coefficient
        if self.actions['down']:
            y += self.speed * coefficient
        if self.actions['left']:
            x -= self.speed * coefficient
        if self.actions['right']:
            x += self.speed * coefficient
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
        """Уменьшает здоровье на dmg"""
        self.current_hp -= dmg

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
        text = [str(self.direction), f'{self.current_hp}/{self.max_hp}',
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
        pygame.draw.line(main_screen, pygame.Color('red'),
                         (x, y),
                         (x + 50 * cos(radians(self.direction)),
                          y + 50 * sin(radians(self.direction))))

    def get_position(self):
        return (self.rect.x + self.rect.width // 2,
                self.rect.y + self.rect.height // 2)

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
        self.counter += 1
        # ограничение счётчика количеством спрайтов
        self.counter %= len(self.current_image_group) * 10
        # собственно, смена спрайта
        self.image = self.current_image_group[int(self.counter / 10)]
        # проверка на повышение уровня
        if self.exp >= self.exp_for_next_level:
            self.exp -= self.exp_for_next_level
            self.exp_for_next_level *= 1.4
            # должно будет вызываться меню апгрейда


class Robot(Player):
    """Персонаж робота"""
    # привязка спрайтов
    idle_images = cut_sheet(load_image("robot_idle.png", -1), 4, 3,
                            mirror_line=2)
    move_images = cut_sheet(load_image("robot_walking.png", -1), 6, 3,
                            mirror_line=2)

    def __init__(self, groups=character):
        super().__init__(groups)
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
        self.weapon = RobotWeapon(self)


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

    def __init__(self, position, text, groups=buttons):
        super().__init__(groups)
        self.state = self.images[0]
        self.image = self.state[0].copy()
        self.rect = self.image.get_rect()
        self.shift = 2
        # инициализация шрифта
        font = pygame.font.SysFont("ComicSans", 30 - len(text))
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
        return self.string_text

    def update(self, pos):
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
    def __init__(self, image, groups=pictures):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect()

    def set_position(self, x, y):
        self.rect = self.rect.move(x, y)

    def set_picture(self, image):
        self.image = image


# меню со своим циклом
# пока открыто, игра приостановлена
def menu(screen):
    pass


# начальный экран со своим циклом
# возвращает выбранного персонажа
def start_screen(screen):
    global clock, options
    running = True
    # инициализация кнопок
    Button((100, 600), "Настройки")
    Button((350, 600), "<")
    Button((480, 600), "Начать")
    Button((610, 600), ">")
    # варианты персонажей
    preview = cut_sheet(load_image("preview.png", -1), 2, 1)[0]
    choice = 0
    image = Picture(preview[choice])
    image.set_position(525, 500)
    while running:
        for event in pygame.event.get():
            # закрытие окна
            if event.type == pygame.QUIT:
                running = False
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
                            return choice

        screen.fill(STRANGE_GREEN)
        buttons.draw(screen)
        buttons.update(pygame.mouse.get_pos())

        pictures.draw(screen)

        clock.tick(FPS)
        pygame.display.flip()
    # окно было закрыто, закрывает программу
    pygame.quit()
    sys.exit()


def main():
    global main_screen, player, clock
    index = start_screen(main_screen)

    running = True
    # инициализация камеры
    camera = Camera()
    # земля
    ground = pygame.sprite.Sprite()
    ground.image = pygame.transform.scale(load_image('ground.png'),
                                          [border_last] * 2)
    ground.rect = ground.image.get_rect()
    all_sprites.add(ground)
    # фон
    # единственный спрайт, которого нет в all_sprites
    background = pygame.sprite.Sprite()
    background.image = pygame.transform.scale(load_image('back.png'),
                                              screen_size)
    background.rect = background.image.get_rect()
    background_group.add(background)

    # инициализация персонажа
    player = eval(options[index] + "()")
    # тестовые объекты
    # Bullet(0, (200, 200), speed=1, radius=4, limit=500)
    for _ in range(8):
        Bat()
    for _ in range(3):
        Demon()
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
        # # заливка фона
        # # можно будет заменить на статичную картинку космоса)
        # main_screen.fill(BLACK)
        background_group.draw(main_screen)

        # изменяем ракурс камеры
        camera.update(player)
        # обновляем положение всех спрайтов
        for sprite in all_sprites:
            camera.apply(sprite)

        # обновление всего
        all_sprites.draw(main_screen)
        all_sprites.update()

        clock.tick(FPS)
        # master(main_screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
