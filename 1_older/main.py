import pygame
import os
import sys
from math import sin, cos, radians


# Изображения не получится загрузить
# без предварительной инициализации pygame
pygame.init()
screen_size = width, height = 900, 700
main_screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption('geme')


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


# Группы спрайтов инициализируются здесь
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
character = pygame.sprite.GroupSingle()


# Ниже классы всего, с чем взаимодействует игрок
class Enemy(pygame.sprite.Sprite):
    # привязка спрайтов
    default_image = load_image("big_demon_idle_anim_f0.png")

    def __init__(self, *groups):
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

    def check_for_targets(self):
        # есть ли игрок в радиусе
        # использует метод get_distance
        pass

    def get_direction(self, x, y):
        # вернёт угол от себя
        # относительно точки (x, y)
        pass

    def get_distance(self, x, y):
        # вернёт расстояние от
        # себя до точки (x, y)
        pass

    def get_damage(self, dmg):
        self.current_hp -= dmg
        pass

    def death(self):
        # смерть врага
        # можно добавить красивых эффектов
        pass

    def update(self):
        # обновление спрайта
        pass


class EnemyExample1(Enemy):
    # привязка спрайтов
    image1 = load_image("big_demon_idle_anim_f0.png")

    def __init__(self, *groups):
        super().__init__(*groups)
        # привязка и так есть /\
        # self.add(enemies)

        self.exp = 50

    def get_exp(self, mod):
        # даёт опыт игроку при своей смерти
        pass

    def attack(self):
        pass

    def special_action(self):
        # особое действие
        # есть не у всех
        pass


class Player(pygame.sprite.Sprite):
    # привязка спрайтов (пока один)
    image1 = load_image("knight_f_idle_anim_f0.png")

    def __init__(self, *groups):
        super().__init__(*groups)

        # я не знаю, для чего это может понадобиться
        self.specifications = None

        # текущий спрайт
        self.image = Player.image1

        # основные параметры
        self.pos_x = 0
        self.pos_y = 0
        self.max_hp = 100
        self.current_hp = 100

        # всё имеющееся оружие (на старте 1-2 шт.)
        self.weapons = []
        # действующее оружие (выбранное)
        self.current_weapon = None

    def update(self):
        # обновление спрайта
        pass

    def move(self, direction):
        # двигает персонажа
        # x, y = direction
        # self.pos_x += x
        # self.pos_y += y
        # или типа того
        pass

    def shoot(self, direction):
        # атакует текущим оружием в направлении курсора
        # self.current_weapon.shoot()
        pass


class Bullet(pygame.sprite.Sprite):
    default_image = load_image("bullet.png")

    # определяется внутри класса weapon при вызове метода shoot
    def __init__(self, *groups, degree, position, speed=20,
                 damage=20, limit=100, pertain=0):
        super().__init__(*groups)
        # спрайты пуль хранятся в оружии,
        # если они, конечно же, нужны
        self.image = Bullet.default_image

        # основные параметры
        self.from_x, self.from_y = position
        self.degree = degree  # в градусах
        self.speed = speed
        self.distance = 0
        self.limit = limit
        self.damage = damage
        self.pertain = pertain

    def move(self):
        # # увеличивает пройденную дистанцию
        # self.distance += self.speed
        # # и на её основе находит текущую точку
        # self.from_x = self.distance * cos(radians(self.degree))
        # self.from_y = self.distance * sin(radians(self.degree))
        # # проверяет лимит
        # if self.distance >= self.limit:
        #     self.death()
        pass

    def check_collision(self):
        pass

    def death(self):
        # удаление/разрушение снаряда
        # можно добавить красивых эффектов
        pass

    def update(self):
        # обновление спрайта
        # также может быть реализован
        # через отрисовку круга (без спрайта)
        pass


class Weapon(pygame.sprite.Sprite):
    # привязка спрайтов снарядов
    default_bullet_image = load_image("bullet.png")

    # привязка спрайтов оружия
    default_weapon_image = load_image("gun.png")

    def __init__(self, reload_speed, distance, damage, mod, bullet_speed, *group):
        super().__init__(*group)

        # текущий спрайт
        self.image = Weapon.default_weapon_image
        self.bullet_sprite = Bullet.default_image  # этот под вопросом

        # основные параметры
        self.bullet_speed = 20
        self.distance = distance
        self.damage = damage
        self.mod = mod

    def shoot(self, direction, position):
        # # создаёт снаряд, летящий из указанной
        # # позиции под указанным углом,
        # # добавляет разброс
        # Bullet(direction, position, self.bullet_speed,
        #        self.damage, self.distance)
        pass


# Эта функция обрабатывает всё, что происходит в игре
def master():
    pass


running = True
FPS = 60
BLACK = pygame.Color('black')
clock = pygame.time.Clock()


def main():
    global running

    # теперь сразу после импортов, чтобы подгрузить спрайты
    # pygame.init()
    # main_screen = pygame.display.set_mode(screen_size)
    # pygame.display.set_caption('geme')

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        main_screen.fill(BLACK)
        clock.tick(FPS)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
