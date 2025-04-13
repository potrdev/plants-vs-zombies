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
font = pg.font.SysFont("montserrat", 32)
bigfont = pg.font.SysFont("montserrat", 45)

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
        pg.draw.rect(screen, color, self.rect, border_radius=5)
        draw_text(self.text, self.rect.x + 5, self.rect.y + 5, (0, 0, 0))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Tower():
    def __init__(self, health, color):
        self.health = health
        self.color = color
        self.x = WIN_X // 2
        self.y = WIN_Y // 1.65

    def take_damage(self, damage):
        self.health -= damage
        if self.health < 0:
            self.health = 0

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
            nearest = min(active_zombies, key=lambda z: self.distance_to(z))
            if self.distance_to(nearest) <= self.shoot_range:
                if PlantTypes[self.ptype] == "Peashooter":
                    if now - self.last_shot > 1300:
                        Bullets.append(Bullet(self.x, self.y, nearest))
                        self.last_shot = now
                elif PlantTypes[self.ptype] == "Double-pea":
                    if now - self.last_shot > 2000:
                        self.last_shot = now
                        self.scheduled_shots.append((now, nearest))
                        self.scheduled_shots.append((now + 190, nearest))

    def update_shots(self):
        now = pg.time.get_ticks()
        for shot_time, target in self.scheduled_shots[:]:
            if now >= shot_time and target.active:
                Bullets.append(Bullet(self.x, self.y, target))
                self.scheduled_shots.remove((shot_time, target))

    def distance_to(self, zombie):
        return math.hypot(self.x - zombie.x, self.y - zombie.y)

class Zombie():
    def __init__(self, x, y, speed, health, coins, color, width, damage):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.health = health
        self.width = width
        self.rect = pg.Rect(self.x - self.width // 2, self.y - self.width // 2, self.width, self.width)
        self.active = True
        self.coins = coins
        self.damage = damage

    def draw(self):
        pg.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.width)

    def move(self, target_x, target_y):
        if not self.active:
            return
        dx, dy = target_x - self.x, target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx /= dist
            dy /= dist
            self.x += dx * self.speed
            self.y += dy * self.speed
        self.rect.topleft = (self.x - self.width // 2, self.y - self.width // 2)

    def attack_tower(self, tower):
        global coins
        if self.active and self.rect.colliderect(pg.Rect(tower.x - 40, tower.y - 40, 80, 80)):
            tower.take_damage(self.damage)
            self.active = False  # Zombie dies on contact
            coins += self.coins

class Bullet:
    def __init__(self, x, y, target):
        self.x = x
        self.y = y
        self.target = target
        self.speed = 10
        self.color = pg.Color("#A4B465")
        self.active = True
        self.width = 10
        self.rect = pg.Rect(self.x - self.width // 2, self.y - self.width // 2, self.width, self.width)

    def move(self):
        if not self.target.active:
            self.active = False
            return
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx /= dist
            dy /= dist
            self.x += dx * self.speed
            self.y += dy * self.speed
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
coins = 125

PlantTypes = ["Peashooter", "Double-pea"]
PlantPrices = [100, 225]
currentPlantIndex = 0
currentPlant = PlantTypes[0]

plant_mode = False
wave_index = 0
last_wave_time = 0
wave_cooldown = 5000
wave_ready = True

zombie_spawn_rate = 3000
next_zombie_spawn_time = 0
current_wave_zombies = []

waves = [
    {"normal": 5, "fast": 0},
    {"normal": 10, "fast": 0},
    {"normal": 15, "fast": 1},
    {"normal": 25, "fast": 3},
    {"normal": 35, "fast": 5},
]

def toggle_plant_mode():
    global plant_mode
    plant_mode = not plant_mode

def select_plant(index):
    global currentPlantIndex, currentPlant
    currentPlantIndex = index
    currentPlant = PlantTypes[index]

plant_button = Button(270, 180, 85, 30, "#9EC6A7", " Plant", toggle_plant_mode, lambda: plant_mode)
plant_type_buttons = [
    Button(175 + i * 150, 75, 130, 30, "#D0EAD9", name, lambda i=i: select_plant(i), lambda i=i: currentPlantIndex == i)
    for i, name in enumerate(PlantTypes)
]

def draw_text(text, x, y, color):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def spawn_zombie(ztype):
    side = random.choice(['top', 'bottom', 'left', 'right'])
    if side == 'top': x, y = random.randint(0, WIN_X), -25
    elif side == 'bottom': x, y = random.randint(0, WIN_X), WIN_Y + 25
    elif side == 'left': x, y = -25, random.randint(0, WIN_Y)
    else: x, y = WIN_X + 25, random.randint(0, WIN_Y)

    if ztype == "normal":
        Zombies.append(Zombie(x, y, 1, 3, 15, "#A27B5C", 25, 10))
    elif ztype == "fast":
        Zombies.append(Zombie(x, y, 2, 2, 20, "#fa692a", 15, 5))

running = True
while running:
    screen.fill("black")
    now = pg.time.get_ticks()

    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if plant_mode and PLANT_ZONE_Y < pos[1] < PLANT_ZONE_Y + PLANT_ZONE_HEIGHT:
                price = PlantPrices[currentPlantIndex]
                if coins >= price:
                    coins -= price
                    Plants.append(Plant(pos[0], pos[1], 300, currentPlantIndex))
            elif plant_button.is_clicked(pos):
                plant_button.callback()
                plant_button.text = "  Exit" if plant_mode else " Plant"
            for b in plant_type_buttons:
                if b.is_clicked(pos):
                    b.callback()

    if wave_index < len(waves) and wave_ready and not current_wave_zombies:
        wave_data = waves[wave_index]
        current_wave_zombies = ["normal"] * wave_data["normal"] + ["fast"] * wave_data["fast"]
        random.shuffle(current_wave_zombies)
        wave_ready = False
        zombie_spawn_rate *= 0.8
        wave_index += 1
        last_wave_time = now
        next_zombie_spawn_time = now

    if current_wave_zombies and now >= next_zombie_spawn_time:
        spawn_zombie(current_wave_zombies.pop(0))
        next_zombie_spawn_time = now + zombie_spawn_rate

    if not wave_ready and not current_wave_zombies and now - last_wave_time >= wave_cooldown:
        wave_ready = True

    pg.draw.rect(screen, "#E1EEBC", ((0, PLANT_ZONE_Y, WIN_X, PLANT_ZONE_HEIGHT)))

    for z in Zombies:
        z.move(Tower.x, Tower.y)
        z.attack_tower(Tower)
        z.draw()

    pg.draw.circle(screen, Tower.color, ((Tower.x, Tower.y)), 40)

    for p in Plants:
        p.draw()
        p.update_shots()
        p.shoot(Zombies)

    for b in Bullets[:]:
        if b.active:
            b.move()
            b.draw()
            for z in Zombies:
                if z.active and b.rect.colliderect(z.rect):
                    z.health -= 1
                    b.active = False
                    if z.health <= 0:
                        coins += z.coins
                        z.active = False
                    break
        if not b.active or b.is_off_screen():
            Bullets.remove(b)

    Zombies[:] = [z for z in Zombies if z.active and z.health > 0]

    pg.draw.rect(screen, "#5b694e", (0, 0, WIN_X, 215))
    pg.draw.rect(screen, "#45523a", (0, 205, WIN_X, 10))
    
    draw_text(f"Tower HP: {Tower.health}", 10, 10, (255, 255, 255))
    
    wave = bigfont.render(f"Wave: {wave_index}/{len(waves)}", True, (200, 255, 200))
    screen.blit(wave, (240, 10))
    
    draw_text(f"Coins: {coins}", WIN_X - 120, 10, (255, 255, 100))

    plant_button.draw()
    for i, b in enumerate(plant_type_buttons):
        b.draw()
        price_color = (0, 255, 0) if coins >= PlantPrices[i] else (255, 60, 60)
        draw_text(f"{PlantPrices[i]}C", b.rect.centerx - 25, b.rect.bottom + 5, price_color)


    if plant_mode:
        mx, my = pg.mouse.get_pos()
        if PLANT_ZONE_Y < my < PLANT_ZONE_Y + PLANT_ZONE_HEIGHT:
            c = pg.Color("#A0C878") if currentPlantIndex == 0 else pg.Color("#55703a")
            c.a = 100
            s = pg.Surface((40, 40), pg.SRCALPHA)
            pg.draw.circle(s, c, (20, 20), 20)
            screen.blit(s, (mx - 20, my - 20))

    clock.tick(FPS)
    pg.display.flip()

pg.quit()
sys.exit()
