import pygame as pg
import sys
import random
import math

pg.init()

WIN_X, WIN_Y = 600, 850
FPS = 60

screen = pg.display.set_mode((WIN_X, WIN_Y))
pg.display.set_caption("Igra")
clock = pg.time.Clock()

class Tower():
    def __init__(self, health, color):
        self.health = health
        self.color = color
        self.x = WIN_X // 2
        self.y = WIN_Y // 1.8

class Plant():
    def __init__(self, x, y, range):
        self.x = x
        self.y = y
        self.color = "#A0C878"
        self.shoot_range = range
    
    def draw(self):
        pg.draw.circle(screen, self.color, (self.x, self.y), 20)

    def shoot(self, zombies):
        if zombies:
            nearest_zombie = min(zombies, key=lambda z: self.distance_to(z))
            if self.distance_to(nearest_zombie) <= self.shoot_range:
                Bullets.append(Bullet(self.x, self.y, nearest_zombie))

    def distance_to(self, zombie):
        return math.sqrt((self.x - zombie.x) ** 2 + (self.y - zombie.y) ** 2)

class Zombie():
    def __init__(self, x, y, speed, health):
        self.x = x
        self.y = y
        self.color = "#A27B5C"
        self.speed = speed
        self.health = health

    def draw(self):
        pg.draw.circle(screen, self.color, (self.x, self.y), 25)

    def move(self, target_x, target_y):
        direction_x = target_x - self.x
        direction_y = target_y - self.y
        distance = math.sqrt(direction_x ** 2 + direction_y ** 2)

        if distance > 0:
            direction_x /= distance
            direction_y /= distance
            self.x += direction_x * self.speed
            self.y += direction_y * self.speed

class Bullet:
    def __init__(self, x, y, target_zombie):
        self.x = x
        self.y = y
        self.target_zombie = target_zombie
        self.speed = 10
        self.color = "#A4B465"
        self.active = True

    def move(self):
        if self.active:
            direction_x = self.target_zombie.x - self.x
            direction_y = self.target_zombie.y - self.y
            distance = (direction_x ** 2 + direction_y ** 2) ** 0.5

            if distance > 0:
                direction_x /= distance
                direction_y /= distance
                self.x += direction_x * self.speed
                self.y += direction_y * self.speed

    def draw(self):
        if self.active:
            pg.draw.circle(screen, self.color, (int(self.x), int(self.y)), 10)

    def is_off_screen(self):
        return self.x < 0 or self.x > WIN_X or self.y < 0 or self.y > WIN_Y

Tower = Tower(100, "#328E6E")
Plants = [] 
Zombies = []
Bullets = []

spawnRate = 3
shootRate = 1

def SpawnZombie():  
    side = random.choice(['top', 'bottom', 'left', 'right'])
    
    if side == 'top':
        x = random.randint(0, WIN_X)
        y = -25
    elif side == 'bottom':
        x = random.randint(0, WIN_X)
        y = WIN_Y + 25
    elif side == 'left':
        x = -25
        y = random.randint(0, WIN_Y)
    elif side == 'right':
        x = WIN_X + 25
        y = random.randint(0, WIN_Y)

    Zombies.append(Zombie(x, y, 1, 3))

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    mousePos = pg.mouse.get_pos()

    # SPAWN ZOMBIE
    if pg.time.get_ticks() % 60 * spawnRate == 0:
        SpawnZombie()

    # PLACE PLANT
    if pg.mouse.get_pressed()[0]:
        Plants.append(Plant(mousePos[0], mousePos[1], 1000))

    # DRAW BACKGROUND
    pg.draw.rect(screen, "#E1EEBC", ((0, WIN_Y // 5, WIN_X, WIN_Y // 1.3)))

    # MOVE / DRAW ZOMBIES
    for zombie in Zombies:
        zombie.move(Tower.x, Tower.y)
        zombie.draw()   

    # DRAW TOWER
    pg.draw.circle(screen, Tower.color, ((Tower.x, Tower.y)), 40)


    # PLANTS SHOOT / DRAW
    for plant in Plants:
        plant.draw()
        
        if pg.time.get_ticks() % 60 * shootRate == 0:
            plant.shoot(Zombies)

    for bullet in Bullets[:]:
        if bullet.active:
            bullet.move()
            bullet.draw()

            for zombie in Zombies[:]:
                if math.sqrt((bullet.x - zombie.x) ** 2 + (bullet.y - zombie.y) ** 2) < 25:
                    zombie.health -= 1
                    bullet.active = False
                    break

            if bullet.is_off_screen():
                bullet.active = False

    for zombie in Zombies:
        if zombie.health <= 0:
            Zombies.remove(zombie)

    clock.tick(FPS)
    pg.display.flip()

pg.quit()
sys.exit()