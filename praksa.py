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

plant_sound = pg.mixer.Sound("plant.wav")
gameover_sound = pg.mixer.Sound("gameover.wav")
shoot_sound = pg.mixer.Sound("shoot.wav")
dead_sound = pg.mixer.Sound("dead.wav")
#background_music = pg.mixer.Sound("music.wav")
#background_music.set_volume(0.1)
#background_music.play(-1)

class Button:
    def __init__(self, x, y, w, h, color, text, callback):
        self.rect = pg.Rect(x, y, w, h)
        self.base_color = color
        self.text = text
        self.callback = callback
        self.active = False

    def draw(self):
        color = pg.Color(self.base_color)
        if self.active:
            color = color.correct_gamma(3)
        pg.draw.rect(screen, color, self.rect, border_radius=5)
        draw_text(self.text, self.rect.x + 40, self.rect.y + 10, (0, 0, 0))

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
            gameover_sound.play()

class Plant():
    def __init__(self, x, y, range, ptype):
        self.x = x
        self.y = y
        self.colors = ["#A0C878", "#55703a", "#81a65d", "#3d5228"]
        self.shoot_range = range
        self.ptype = ptype
        self.last_shot = 0
        self.scheduled_shots = []
        
        if self.ptype == 0:
            self.image = pg.image.load('peashooter.png').convert_alpha()
        else:
            self.image = pg.image.load('doublepea.png').convert_alpha()
        self.image = pg.transform.scale(self.image, (80, 80))
        self.original_image = self.image

    def draw(self):
        nearest_enemy = self.get_nearest_enemy()
        if nearest_enemy:
            angle = self.angle_to(nearest_enemy)
            self.image = pg.transform.rotate(self.original_image, -angle-90)
            image_rect = self.image.get_rect(center=(self.x, self.y))
            screen.blit(self.image, image_rect.topleft)
        else:
            image_rect = self.original_image.get_rect(center=(self.x, self.y))
            screen.blit(self.original_image, image_rect.topleft)

    def shoot(self, zombies):
        now = pg.time.get_ticks()
        active_zombies = [z for z in zombies if z.active]
        if active_zombies:
            nearest = min(active_zombies, key=lambda z: self.distance_to(z))
            if self.distance_to(nearest) <= self.shoot_range:
                if PlantTypes[self.ptype] == "Peashooter":
                    if now - self.last_shot > 1300:
                        Bullets.append(Bullet(self.x, self.y, nearest))
                        shoot_sound.play()
                        self.last_shot = now
                elif PlantTypes[self.ptype] == "Double-pea":
                    if now - self.last_shot > 2000:
                        self.last_shot = now
                        self.scheduled_shots.append((now, nearest))
                        shoot_sound.play()
                        self.scheduled_shots.append((now + 190, nearest))
                        shoot_sound.play()

    def update_shots(self):
        now = pg.time.get_ticks()
        for shot_time, target in self.scheduled_shots[:]:
            if now >= shot_time and target.active:
                Bullets.append(Bullet(self.x, self.y, target))
                self.scheduled_shots.remove((shot_time, target))

    def distance_to(self, zombie):
        return math.hypot(self.x - zombie.x, self.y - zombie.y)

    def get_nearest_enemy(self):
        active_zombies = [z for z in Zombies if z.active]
        if active_zombies:
            return min(active_zombies, key=lambda z: self.distance_to(z))
        return None

    def angle_to(self, zombie):
        dx = zombie.x - self.x
        dy = zombie.y - self.y
        return math.degrees(math.atan2(dy, dx))

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
        pg.draw.circle(screen, pg.Color(self.color).correct_gamma(1.5), (int(self.x), int(self.y)), self.width, 4)

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
            self.active = False
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
            pg.draw.circle(screen, "#818f4a", (int(self.x), int(self.y)), self.width, 2)

    def is_off_screen(self):
        return self.x < 0 or self.x > WIN_X or self.y < 0 or self.y > WIN_Y

Tower = Tower(100, "#328E6E")
Plants = []
Zombies = []
Bullets = []
coins = 200

PlantTypes = ["Peashooter", "Double-pea"]
PlantPrices = [100, 225]
currentPlantIndex = -1
plant_mode = False
wave_index = 0
last_wave_time = 0
wave_cooldown = 5000
wave_ready = True

zombie_spawn_rate = 3000
next_zombie_spawn_time = 0
current_wave_zombies = []

waves = [
    {"normal": 5, "fast": 0,  "big": 0},
    {"normal": 10, "fast": 1, "big": 0},
    {"normal": 15, "fast": 3, "big": 1},
    {"normal": 25, "fast": 5, "big": 2},
    {"normal": 35, "fast": 10, "big": 3},
]

def toggle_plant_mode(index):
    global plant_mode, currentPlantIndex
    if currentPlantIndex == index:
        plant_mode = not plant_mode
        if not plant_mode:
            currentPlantIndex = -1
            for button in plant_type_buttons:
                button.active = False
    else:
        currentPlantIndex = index
        plant_mode = True
        for button in plant_type_buttons:
            button.active = False
        plant_type_buttons[index].active = True

plant_type_buttons = [
    Button(175 + i * 150, 75, 130, 100, "#D0EAD9", f"${PlantPrices[i]}", lambda i=i: toggle_plant_mode(i))
    for i in range(len(PlantTypes))
]

def draw_text(text, x, y, color):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def spawn_zombie (ztype):
    side = random.choice(['top', 'bottom', 'left', 'right'])
    if side == 'top': x, y = random.randint(0, WIN_X), -25
    elif side == 'bottom': x, y = random.randint(0, WIN_X), WIN_Y + 25
    elif side == 'left': x, y = -25, random.randint(0, WIN_Y)
    else: x, y = WIN_X + 25, random.randint(0, WIN_Y)

    if ztype == "normal":
        Zombies.append(Zombie(x, y, 1, 5, 15, "#A27B5C", 25, 10))
    elif ztype == "fast":
        Zombies.append(Zombie(x, y, 2, 5, 20, "#fa692a", 15, 5))
    elif ztype == "big":
        Zombies.append(Zombie(x, y, 0.5, 40, 100, "#fa692a", 60, 25))

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
                    plant_sound.play()
                    
                    for button in plant_type_buttons:
                        button.active = False
                    
                    plant_mode = False
                    currentPlantIndex = -1
            for b in plant_type_buttons:
                if b.is_clicked(pos):
                    b.callback()

    if wave_index < len(waves) and wave_ready and not current_wave_zombies:
        wave_data = waves[wave_index]
        current_wave_zombies = ["normal"] * wave_data["normal"] + ["fast"] * wave_data["fast"] + ["big"] * wave_data["big"]
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

    bg = pg.image.load('grass.jpg').convert_alpha()
    bg = pg.transform.scale(bg, (WIN_X, WIN_Y))
    screen.blit(bg, (0,0))

    for z in Zombies:
        z.move(Tower.x, Tower.y)
        z.attack_tower(Tower)
        z.draw()

    pg.draw.circle(screen, Tower.color, ((Tower.x, Tower.y)), 40)
    pg.draw.circle(screen, "#1f664d", ((Tower.x, Tower.y)), 40, 5)

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
                    dead_sound.play()
                    if z.health <= 0:
                        coins += z.coins
                        z.active = False
                    break
        if not b.active or b.is_off_screen():
            Bullets.remove(b)

    Zombies[:] = [z for z in Zombies if z.active and z.health > 0]

    pg.draw.rect(screen, "#5b694e", (0, 0, WIN_X, 215))
    pg.draw.rect(screen, "#45523a", (0, 205, WIN_X, 10))
    
    draw_text(f"{Tower.health}", WIN_X // 2 - 20, WIN_Y // 1.65 - 8, "black")
    draw_text(f"{Tower.health}", WIN_X // 2 - 20, WIN_Y // 1.65 - 10, (255, 255, 255))
    
    waveoutline = bigfont.render(f"Wave: {wave_index}/{len(waves)}", True, "black")
    screen.blit(waveoutline, (242, 10))
    wave = bigfont.render(f"Wave: {wave_index}/{len(waves)}", True, "white")
    screen.blit(wave, (240, 10))
    
    draw_text(f"${coins}", WIN_X // 2- 18, 45, "#36360c")
    draw_text(f"${coins}", WIN_X // 2- 20, 45, (255, 255, 100))

    for i, b in enumerate(plant_type_buttons):
        b.draw()
        
    peashooterui = pg.image.load('peashooter.png').convert_alpha()
    peashooterui = pg.transform.scale(peashooterui, (70, 70))
    screen.blit(peashooterui, ((207, 105)))
    
    doublepeaui = pg.image.load('doublepea.png').convert_alpha()
    doublepeaui = pg.transform.scale(doublepeaui, (70, 70))
    screen.blit(doublepeaui, ((353, 105)))
    
    if plant_mode:
        mx, my = pg.mouse.get_pos()
        if PLANT_ZONE_Y < my < PLANT_ZONE_Y + PLANT_ZONE_HEIGHT:
            c = pg.Color("#5d9ac9")
            c.a = 150
            s = pg.Surface((40, 40), pg.SRCALPHA)
            pg.draw.circle(s, c, (20, 20), 20)
            screen.blit(s, (mx - 20, my - 20))

    clock.tick(FPS)
    pg.display.flip()

pg.quit()
sys.exit()
