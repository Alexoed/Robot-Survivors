import pygame

import os
import sys
from math import sin, cos, radians, atan, sqrt, degrees


BLACK = pygame.Color('black')
YELLOW = pygame.Color('yellow')
GREY = pygame.Color('grey')

UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
# Изображения не получится загрузить
# без предварительной инициализации pygame
pygame.init()
screen_size = width, height = 900, 700
main_screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption('geme')
border_first = 0
border_last = 1000


def load_image(name, colorkey=None):
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
    return pygame.transform.flip(image, True, False)


def cut_sheet(sheet, columns, rows, mirror_line=-1):
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


# Группы спрайтов инициализируются здесь
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
character = pygame.sprite.GroupSingle()


# Ниже классы всего, с чем взаимодействует игрок
class Enemy(pygame.sprite.Sprite):
    # привязка спрайтов
    default_image = load_image("big_demon_idle_anim_f0.png")

    def __init__(self, groups=enemies):
        super().__init__(*groups)

        # добавление в группу ко всем спрайтам
        self.add(all_sprites)

        # текущий спрайт
        self.image = Enemy.default_image

        # основные параметры
        self.max_hp = 100
        self.current_hp = 100
        self.speed = 10
        # позиция выбирается случайно,
        # где одна переменная равна нулю,
        # а другая случайному числу
        # в границах поля
        self.pos_x = 0
        self.pos_y = 0

        self.weapon = None

    def check_for_target(self, x, y):
        """Проверка на то, возможно ли атаковать игрока"""
        if self.weapon is not None and \
           self.weapon.distance >= self.get_distance(x, y) and \
           self.weapon.reload == 0:
            return True
        return False

    def get_direction(self, x, y):
        """Вернёт угол от себя относительно
        точки с координатами (x, y)"""
        direction = degrees(atan((x - self.rect.x) / (y - self.rect.y)))
        if y - self.rect.y < 0:
            direction += 180
        return direction

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

    def get_exp(self, mod):
        """Даёт опыт игроку при своей смерти"""
        pass

    def death(self):
        """События смерти врага"""
        # можно добавить красивых эффектов
        enemies.remove(self)
        del self

    def update(self, player_x, player_y):
        """Обновление спрайта"""
        self.move(self.get_direction(player_x, player_y))
        if self.check_for_target(player_x, player_y):
            self.weapon.shoot(self.get_direction(player_x, player_y),
                              (self.rect.x, self.rect.y))


class EnemyExample1(Enemy):
    # привязка спрайтов
    image1 = load_image("big_demon_idle_anim_f0.png")

    def __init__(self, groups=enemies):
        super().__init__(*groups)
        # привязка и так есть /\
        # self.add(enemies)

        self.exp = 50

    def get_exp(self, mod):
        """Даёт опыт игроку при своей смерти"""
        pass

    def attack(self):
        """Производит эффект атаки"""
        pass

    def special_action(self):
        """Особое свойство/действие/эффект
        конкретного врага. Есть не у всех."""
        pass


class Bullet(pygame.sprite.Sprite):
    # определяется внутри класса weapon при вызове метода shoot

    def __init__(self, degree, position, speed=20, damage=20, limit=100,
                 pertain=0, radius=2, colour=YELLOW, *groups):
        super().__init__(*groups)
        # спрайты пуль хранятся в оружии,
        # если они, конечно же, нужны
        self.radius = radius
        self.colour = colour

        # основные параметры
        self.from_x, self.from_y = position
        self.degree = degree  # в градусах
        self.speed = speed
        self.distance = 0
        self.limit = limit
        self.damage = damage
        self.pertain = pertain

    def move(self):
        """Двигает снаряд"""
        # увеличивает пройденную дистанцию
        self.distance += self.speed
        # и на её основе находит текущую точку
        self.from_x = self.distance * cos(radians(self.degree))
        self.from_y = self.distance * sin(radians(self.degree))
        # проверяет лимит
        if self.distance >= self.limit:
            self.death()

    def check_collision(self):
        pass

    def death(self):
        """Удаление снаряда из игры"""
        # можно добавить красивых эффектов
        pass

    def update(self):
        """Обновление спрайта"""
        # рисование кружка
        # с радиусом self.radius
        # и цветом self.colour
        pass


class Weapon(pygame.sprite.Sprite):
    # привязка спрайтов оружия
    default_weapon_image = load_image("gun.png")

    def __init__(self, *group):
        super().__init__(*group)

        # текущий спрайт
        self.image = Weapon.default_weapon_image
        self.bullet_size = 2
        self.bullet_colour = YELLOW

        # основные параметры
        self.reload_speed = 6
        self.bullet_speed = 20
        self.bullet_pertain = 0
        self.distance = 100
        self.damage = 5
        self.mod = 1

    def shoot(self, direction, position):
        """Создаёт снаряд, летящий из указанной
        позиции под указанным углом, добавляет разброс"""
        Bullet(direction, position, self.bullet_speed, self.damage,
               self.distance, self.bullet_pertain, self.bullet_size,
               self.bullet_colour, bullets)
        pass


class TestWeapon1(Weapon):
    image1 = load_image("minigun.png")

    def __init__(self, *group):
        super().__init__(*group)

        self.image = TestWeapon1.image1
        self.reload_speed = 2
        self.bullet_size = 2
        self.bullet_colour = GREY
        self.bullet_speed = 40
        self.damage = 4


class Player(pygame.sprite.Sprite):
    # привязка спрайтов
    # image1 = load_image("knight_f_idle_anim_f0.png")
    idle_images = cut_sheet(load_image("robot_idle.png", -1), 4, 3,
                            mirror_line=2)
    move_images = cut_sheet(load_image("robot_walking.png", -1), 6, 3,
                            mirror_line=2)

    def __init__(self, *groups):
        super().__init__(*groups)

        # текущий спрайт
        self.counter = 0
        self.group = 0
        self.current_image_group = Player.idle_images[self.group]
        self.image = self.current_image_group[self.counter]
        self.rect = self.image.get_rect()

        # основные параметры
        self.rect.x = 10
        self.rect.y = 10
        self.max_hp = 100
        self.current_hp = 100
        self.speed = 4
        self.direction = 0
        # перемещение [up, down, left, right]
        self.move_vars = {'up': False, 'down': False,
                          'left': False, 'right': False}

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
        if any(self.move_vars.values()):
            self.current_image_group = Player.move_images[self.group]
        else:
            self.current_image_group = Player.idle_images[self.group]

    def move(self):
        """Перемещает игрока"""
        x, y = 0, 0
        if self.move_vars['up']:
            y -= self.speed
        if self.move_vars['down']:
            y += self.speed
        if self.move_vars['left']:
            x -= self.speed
        if self.move_vars['right']:
            x += self.speed
        if not(border_first < self.rect.x + x < border_last):
            x = 0
        if not(border_first < self.rect.y + y < border_last):
            y = 0
        self.rect = self.rect.move(x, y)

    def set_movement(self, index, value=True):
        """Устанавливает перемещение игрока"""
        self.move_vars[index] = value

    def shoot(self, direction):
        """Атакует текущим оружием в направлении курсора"""
        if self.weapon.reload == 0:
            self.weapon.shoot(direction, (self.rect.x, self.rect.y))
        else:
            pass  # звук/эффект невозможности совершения атаки

    def debug_view(self):
        """Функция отладки, показывает
        направление игрока к курсору и угол"""
        global main_screen
        font = pygame.font.Font(None, 20)
        string_rendered = font.render(str(self.direction), True,
                                      pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        intro_rect.top = 0
        intro_rect.x = 0
        main_screen.blit(string_rendered, intro_rect)
        x = self.rect.x + self.rect.width // 2
        y = self.rect.y + self.rect.height // 2
        pygame.draw.line(main_screen, pygame.Color('red'),
                         (x, y),
                         (x + 50 * cos(radians(self.direction)),
                          y + 50 * sin(radians(self.direction))))

    def update(self):
        """Обновление спрайта"""
        # self.debug_view()
        # движение
        self.move()
        # обзор (на случай бездействия курсора)
        # думаю, не понадобится после добавления камеры
        self.set_direction(None)
        # счётчик смены спрайтов
        self.counter += 1
        # ограничение счётчика количеством спрайтов
        self.counter %= len(self.current_image_group) * 10
        # собственно, смена спрайта
        self.image = self.current_image_group[int(self.counter / 10)]


# Эта функция обрабатывает всё, что происходит в игре
def master(screen):
    # if pygame.mouse.get_focused():
    #     cursor_group.draw(screen)
    pass


# меню со своим циклом
# пока открыто, игра приостановлена
def menu(screen):
    pass


# начальный экран со своим циклом
# возвращает выбранного персонажа
def start_screen():
    pass


running = True
FPS = 60
clock = pygame.time.Clock()


def main():
    global running, clock, main_screen
    # инициализация персонажа
    player = Player(character)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                # направление движения персонажа
                if event.key in UP_KEYS:
                    player.set_movement('up')
                elif event.key in DOWN_KEYS:
                    player.set_movement('down')
                if event.key in RIGHT_KEYS:
                    player.set_movement('right')
                elif event.key in LEFT_KEYS:
                    player.set_movement('left')

                if event.key == pygame.K_ESCAPE:
                    # пауза/меню
                    menu(main_screen)
            if event.type == pygame.KEYUP:
                # прекращение движения персонажа
                if event.key in UP_KEYS:
                    player.set_movement('up', False)
                elif event.key in DOWN_KEYS:
                    player.set_movement('down', False)
                if event.key in RIGHT_KEYS:
                    player.set_movement('right', False)
                elif event.key in LEFT_KEYS:
                    player.set_movement('left', False)
            if event.type == pygame.MOUSEMOTION:
                # устанавливаем обзор на курсор
                player.set_direction(event.pos)
        # заливка фона
        # можно будет заменить на статичную картинку космоса)
        main_screen.fill(BLACK)

        # обновление персонажа
        # в дальнейшем обновление всего
        character.draw(main_screen)
        character.update()

        clock.tick(FPS)
        # master(main_screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
