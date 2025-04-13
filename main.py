import pygame as pg
import pygame.freetype
import sys
import random
import math

pg.init()
pg.freetype.init()

WIN_X, WIN_Y = 600, 850
FPS = 60

screen = pg.display.set_mode((WIN_X, WIN_Y))
pg.display.set_caption("Igra")
clock = pg.time.Clock()
font = pg.font.SysFont("montserrat", 24)
emoji_font = pg.freetype.Font("NotoColorEmoji-Regular.ttf", 28)

PLANT_ZONE_Y = WIN_Y // 4
PLANT_ZONE_HEIGHT = int(WIN_Y // 1.3)

class Button:
    def __init__(self, x, y, w, h, color, text, callback, is_active_fn=None):
        self.rect = pg.Rect(x, y, w, h)
        self.base_color = color
        self.text = text
        self.callback = callback
        self.is_active_fn = is_active_fn

    def draw(self):
        color = pg.Color(self.base_color)
        if self.is_active_fn and self.is_active_fn():
            color = color.correct_gamma(0.5)
        pg.draw.rect(screen, color, self.rect)
        emoji_font.render_to(screen, (self.rect.x + 8, self.rect.y + 3), self.text, (0, 0, 0))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Tower():
    def __init__(self, health, color):
        self.health = health
        self.color = color
        self.x = WIN_X // 2
        self.y = WIN_Y // 1.65

class Plant():
    def __init__(self, x, y, range, ptype):
        self.x = x
        self.y = y
        self.colors = ["#A0C878", "#55703a"]
        self.shoot_range = range
        self.ptype = ptype

        self.last_shot = 0
        self.scheduled_shots = []

    def draw(self):
        pg.draw.circle(screen, self.colors[self.ptype], (self.x, self.y), 20)

    def shoot(self, zombies):
        now = pg.time.get_ticks()
        active_zombies = [z for z in zombies if z.active]
        if active_zombies:
            nearest_zombie = min(active_zombies, key=lambda z: self.distance_to(z))
            if self.distance_to(nearest_zombie) <= self.shoot_range:
                if "Peashooter" == PlantTypes[self.ptype]:
                    if now - self.last_shot > 500:
                        Bullets.append(Bullet(self.x, self.y, nearest_zombie))
                        self.last_shot = now
                elif "Double-pea" == PlantTypes[self.ptype]:
                    if now - self.last_shot > 800:
                        self.last_shot = now
                        self.scheduled_shots.append((now, nearest_zombie))
                        self.scheduled_shots.append((now + 300, nearest_zombie))

    def update_shots(self):
        now = pg.time.get_ticks()
        for shot_time, target in self.scheduled_shots[:]:
            if now >= shot_time:
                if target.active:
                    Bullets.append(Bullet(self.x, self.y, target))
                self.scheduled_shots.remove((shot_time, target))

    def distance_to(self, zombie):
        return math.sqrt((self.x - zombie.x) ** 2 + (self.y - zombie.y) ** 2)

class Zombie():
    def __init__(self, x, y, speed, health, coins, color, width):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.health = health
        self.width = width
        self.rect = pg.Rect(self.x - self.width // 2, self.y - self.width // 2, self.width, self.width)
        self.active = True
        self.coins = coins

    def draw(self):
        pg.draw.circle(screen, self.color, (self.x, self.y), self.width)

    def move(self, target_x, target_y):
        if self.active:
            direction_x = target_x - self.x
            direction_y = target_y - self.y
            distance = math.sqrt(direction_x ** 2 + direction_y ** 2)
            if distance > 0:
                direction_x /= distance
                direction_y /= distance
                self.x += direction_x * self.speed
                self.y += direction_y * self.speed
            self.rect.topleft = (self.x - self.width // 2, self.y - self.width // 2)

    def is_colliding(self, bullet):
        return self.rect.colliderect(bullet.rect)

class Bullet:
    def __init__(self, x, y, target_zombie):
        self.x = x
        self.y = y
        self.target_zombie = target_zombie
        self.speed = 10
        self.color = pg.Color("#A4B465")
        self.active = True
        self.width = 10
        self.rect = pg.Rect(self.x - self.width // 2, self.y - self.width // 2, self.width, self.width)

    def move(self):
        if not self.target_zombie.active:
            self.active = False
            return
        direction_x = self.target_zombie.x - self.x
        direction_y = self.target_zombie.y - self.y
        distance = math.sqrt(direction_x ** 2 + direction_y ** 2)
        if distance > 0:
            direction_x /= distance
            direction_y /= distance
            self.x += direction_x * self.speed
            self.y += direction_y * self.speed
        self.rect.topleft = (self.x - self.width // 2, self.y - self.width // 2)

    def draw(self):
        if self.active:
            pg.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.width)

    def is_off_screen(self):
        return self.x < 0 or self.x > WIN_X or self.y < 0 or self.y > WIN_Y

Tower = Tower(100, "#328E6E")
Plants = [] 
Zombies = []
Bullets = []
coins = 500

PlantTypes = ["Peashooter", "Double-pea"]
PlantPrices = [50, 75]
currentPlantIndex = 0
currentPlant = PlantTypes[0]

plant_mode = False

def toggle_plant_mode():
    global plant_mode
    plant_mode = not plant_mode
    plant_button.text = "❌" if plant_mode else "🏗️"

def select_plant(index):
    global currentPlantIndex, currentPlant
    currentPlantIndex = index
    currentPlant = PlantTypes[index]

plant_button = Button(10, 75, 50, 40, "#9EC6A7", "🏗️", toggle_plant_mode, lambda: plant_mode)
plant_type_buttons = [
    Button(80 + i * 110, 75, 100, 40, "#D0EAD9", "🌿" if name == "Peashooter" else "🌱🌱", lambda i=i: select_plant(i), lambda i=i: currentPlantIndex == i)
    for i, name in enumerate(PlantTypes)
]

waves = [
    [("normal", 5), ("fast", 2)],
    [("normal", 7), ("fast", 5)],
    [("normal", 10), ("fast", 8)],
]
current_wave = 0
wave_in_progress = False
wave_cooldown = 5000
last_wave_time = -wave_cooldown
zombies_to_spawn = []
zombie_spawn_delay = 800
last_zombie_spawn = 0

def start_next_wave():
    global wave_in_progress, zombies_to_spawn, current_wave, last_wave_time
    if current_wave < len(waves):
        zombies_to_spawn = []
        for ztype, count in waves[current_wave]:
            zombies_to_spawn.extend([ztype] * count)
        wave_in_progress = True
        current_wave += 1
        last_wave_time = pg.time.get_ticks()

def SpawnZombie(zombieType):
    side = random.choice(['top', 'bottom', 'left', 'right'])
    if side == 'top': x, y = random.randint(0, WIN_X), -25
    elif side == 'bottom': x, y = random.randint(0, WIN_X), WIN_Y + 25
    elif side == 'left': x, y = -25, random.randint(0, WIN_Y)
    else: x, y = WIN_X + 25, random.randint(0, WIN_Y)

    if zombieType == "normal":
        Zombies.append(Zombie(x, y, 1, 3, 5, "#A27B5C", 25))
    elif zombieType == "fast":
        Zombies.append(Zombie(x, y, 2, 2, 10, "#fa692a", 15))

def draw_text(text, x, y, color):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

running = True
while running:
    screen.fill("black")

    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = event.pos
                if plant_mode and PLANT_ZONE_Y < pos[1] < PLANT_ZONE_Y + PLANT_ZONE_HEIGHT:
                    plant_price = PlantPrices[currentPlantIndex]
                    if coins >= plant_price:
                        coins -= plant_price
                        Plants.append(Plant(pos[0], pos[1], 300, currentPlantIndex))
                else:
                    if plant_button.is_clicked(pos):
                        plant_button.callback()
                    for b in plant_type_buttons:
                        if b.is_clicked(pos):
                            b.callback()

    now = pg.time.get_ticks()
    if not wave_in_progress and now - last_wave_time >= wave_cooldown:
        start_next_wave()

    if wave_in_progress and zombies_to_spawn and now - last_zombie_spawn > zombie_spawn_delay:
        SpawnZombie(zombies_to_spawn.pop(0))
        last_zombie_spawn = now
        if not zombies_to_spawn:
            wave_in_progress = False
            last_wave_time = now

    pg.draw.rect(screen, "#E1EEBC", ((0, PLANT_ZONE_Y, WIN_X, PLANT_ZONE_HEIGHT)))

    for zombie in Zombies:
        zombie.move(Tower.x, Tower.y)
        zombie.draw()

    pg.draw.circle(screen, Tower.color, ((Tower.x, Tower.y)), 40)

    for plant in Plants:
        plant.draw()
        plant.update_shots()
        plant.shoot(Zombies)

    for bullet in Bullets[:]:
        if bullet.active:
            bullet.move()
            bullet.draw()
            for zombie in Zombies[:]:
                if zombie.active and bullet.rect.colliderect(zombie.rect):
                    zombie.health -= 1
                    bullet.active = False
                    if zombie.health <= 0:
                        coins += zombie.coins
                        zombie.active = False
                    break
        if not bullet.active or bullet.is_off_screen():
            Bullets.remove(bullet)

    for zombie in Zombies[:]:
        if not zombie.active or zombie.health <= 0:
            Zombies.remove(zombie)

    pg.draw.rect(screen, "#5b694e", (0, 0, WIN_X, 215))
    pg.draw.rect(screen, "#45523a", (0, 205, WIN_X, 10))

    draw_text(f"Tower HP: {Tower.health}", 10, 10, (255,255,255))
    draw_text(f"Wave {current_wave}/{len(waves)}", 10, 40, (255,255,255))
    draw_text(f"Coins: {coins}", WIN_X - 150, 10, (255,255,255))

    plant_button.draw()
    for i, b in enumerate(plant_type_buttons):
        b.draw()
        draw_text(f"{PlantPrices[i]}C", b.rect.centerx - 15, b.rect.bottom + 5, (255, 255, 255))

    if plant_mode:
        mouse_x, mouse_y = pg.mouse.get_pos()
        if PLANT_ZONE_Y < mouse_y < PLANT_ZONE_Y + PLANT_ZONE_HEIGHT:
            preview_color = pg.Color("#A0C878") if currentPlantIndex == 0 else pg.Color("#55703a")
            preview_color.a = 100
            s = pg.Surface((40, 40), pg.SRCALPHA)
            pg.draw.circle(s, preview_color, (20, 20), 20)
            screen.blit(s, (mouse_x - 20, mouse_y - 20))

    clock.tick(FPS)
    pg.display.flip()

pg.quit()
sys.exit()
