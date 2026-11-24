import pygame
import math
import random
import sys

pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vice City Mini")
clock = pygame.time.Clock()

font_ui = pygame.font.SysFont("arial", 22, bold=True)
font_stars = pygame.font.SysFont("arial", 26, bold=True)
font_small = pygame.font.SysFont("arial", 16)

C_ASPHALT = (42, 42, 48)
C_SIDEWALK = (85, 85, 95)
C_LINE = (230, 190, 40)
C_WHITE = (255, 255, 255)
C_BLACK = (15, 15, 15)
C_GOLD = (255, 215, 0)
C_RED = (230, 50, 60)
C_BLUE = (40, 100, 240)
C_NEON_PINK = (255, 80, 180)
C_NEON_CYAN = (0, 235, 235)

WORLD_SIZE = 2400
BLOCK_SIZE = 400
ROAD_WIDTH = 90

buildings = []
building_colors = [(215, 115, 155), (95, 195, 210), (230, 165, 95), (165, 140, 215), (220, 220, 230)]

for gx in range(0, WORLD_SIZE, BLOCK_SIZE):
    for gy in range(0, WORLD_SIZE, BLOCK_SIZE):
        if gx == 800 and gy == 800:
            continue
        bx = gx + ROAD_WIDTH // 2 + 25
        by = gy + ROAD_WIDTH // 2 + 25
        bw = BLOCK_SIZE - ROAD_WIDTH - 50
        bh = BLOCK_SIZE - ROAD_WIDTH - 50
        buildings.append({
            "rect": pygame.Rect(bx, by, bw, bh),
            "color": random.choice(building_colors),
            "accent": C_NEON_PINK if random.random() > 0.5 else C_NEON_CYAN
        })

class Car:
    def __init__(self, x, y, color, is_police=False):
        self.x, self.y = float(x), float(y)
        self.angle = random.uniform(0, 360)
        self.speed = 0.0
        self.max_speed = 9.5 if not is_police else 8.8
        self.color = color
        self.is_police = is_police
        self.siren_timer = 0

    def get_rect(self):
        return pygame.Rect(self.x - 18, self.y - 18, 36, 36)

    def update_player(self, keys):
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.speed += 0.25
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.speed -= 0.20
        else:
            self.speed *= 0.96

        turn_mult = 1.45 if keys[pygame.K_SPACE] else 1.0
        if keys[pygame.K_SPACE]:
            self.speed *= 0.96

        self.speed = max(-self.max_speed * 0.45, min(self.max_speed, self.speed))

        if abs(self.speed) > 0.3:
            direction = 1 if self.speed > 0 else -1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.angle -= 3.6 * turn_mult * direction
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.angle += 3.6 * turn_mult * direction

        self.move_and_collide()

    def update_police(self, target_x, target_y, wanted_level):
        self.siren_timer += 1
        target_angle = math.degrees(math.atan2(target_y - self.y, target_x - self.x))
        diff = (target_angle - self.angle + 180) % 360 - 180
        self.angle += max(-3.2, min(3.2, diff))
        chase_speed = min(self.max_speed, 5.2 + wanted_level * 0.75)
        self.speed += (chase_speed - self.speed) * 0.08
        self.move_and_collide()

    def move_and_collide(self):
        rad = math.radians(self.angle)
        old_x, old_y = self.x, self.y
        self.x = max(30, min(WORLD_SIZE - 30, self.x + math.cos(rad) * self.speed))
        self.y = max(30, min(WORLD_SIZE - 30, self.y + math.sin(rad) * self.speed))
        car_rect = self.get_rect()
        for b in buildings:
            if car_rect.colliderect(b["rect"]):
                self.x, self.y = old_x, old_y
                self.speed = -self.speed * 0.4
                break

    def draw(self, surface, cam_x, cam_y):
        car_surf = pygame.Surface((48, 26), pygame.SRCALPHA)
        pygame.draw.rect(car_surf, self.color, (0, 0, 48, 26), border_radius=5)
        pygame.draw.rect(car_surf, (25, 30, 40), (32, 3, 9, 20), border_radius=2)
        pygame.draw.rect(car_surf, (25, 30, 40), (6, 4, 6, 18), border_radius=2)
        pygame.draw.rect(car_surf, (255, 255, 180), (45, 2, 3, 5))
        pygame.draw.rect(car_surf, (255, 255, 180), (45, 19, 3, 5))
        if self.is_police:
            flash = (self.siren_timer // 8) % 2 == 0
            pygame.draw.rect(car_surf, C_RED if flash else C_BLUE, (21, 3, 6, 10))
            pygame.draw.rect(car_surf, C_BLUE if flash else C_RED, (21, 13, 6, 10))
        rotated = pygame.transform.rotate(car_surf, -self.angle)
        surface.blit(rotated, rotated.get_rect(center=(self.x - cam_x, self.y - cam_y)))

class Pedestrian:
    def __init__(self):
        self.respawn()
        self.color = (random.randint(120, 255), random.randint(120, 255), random.randint(120, 255))
        self.angle = random.uniform(0, 360)
        self.timer = random.randint(60, 180)

    def respawn(self):
        while True:
            self.x = random.randint(100, WORLD_SIZE - 100)
            self.y = random.randint(100, WORLD_SIZE - 100)
            if not any(pygame.Rect(self.x - 10, self.y - 10, 20, 20).colliderect(b["rect"]) for b in buildings):
                break

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.angle = random.uniform(0, 360)
            self.timer = random.randint(60, 180)
        rad = math.radians(self.angle)
        nx, ny = self.x + math.cos(rad) * 1.3, self.y + math.sin(rad) * 1.3
        if 40 < nx < WORLD_SIZE - 40 and 40 < ny < WORLD_SIZE - 40 and not any(pygame.Rect(nx - 8, ny - 8, 16, 16).colliderect(b["rect"]) for b in buildings):
            self.x, self.y = nx, ny
        else:
            self.angle += 180

    def draw(self, surface, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        pygame.draw.circle(surface, self.color, (sx, sy), 7)
        pygame.draw.circle(surface, C_BLACK, (sx, sy), 7, 1)

player_x, player_y = 1000.0, 1000.0
in_vehicle, current_car, wanted_level, cash = False, None, 0, 0
cars = [Car(1060, 980, C_NEON_PINK), Car(920, 1050, C_NEON_CYAN), Car(1400, 1000, C_GOLD), Car(600, 1400, (255, 100, 40)), Car(1800, 600, (180, 70, 255))]
police_cars = []
pedestrians = [Pedestrian() for _ in range(45)]
cash_pickups = [pygame.Rect(random.randint(100, WORLD_SIZE - 100), random.randint(100, WORLD_SIZE - 100), 18, 18) for _ in range(25)]

def add_wanted():
    global wanted_level
    if wanted_level < 5:
        wanted_level += 1
        ang = random.uniform(0, math.pi * 2)
        px = max(80, min(WORLD_SIZE - 80, player_x + math.cos(ang) * 480))
        py = max(80, min(WORLD_SIZE - 80, player_y + math.sin(ang) * 480))
        cop = Car(px, py, (25, 35, 80), is_police=True)
        police_cars.append(cop)
        cars.append(cop)

running = True
while running:
    clock.tick(60)
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                if not in_vehicle:
                    for car in cars:
                        if math.hypot(player_x - car.x, player_y - car.y) < 55:
                            in_vehicle, current_car = True, car
                            break
                else:
                    in_vehicle = False
                    rad = math.radians(current_car.angle + 90)
                    player_x, player_y = current_car.x + math.cos(rad) * 32, current_car.y + math.sin(rad) * 32
                    current_car = None
            if event.key == pygame.K_c:
                wanted_level = 0
                for cop in police_cars:
                    if cop in cars:
                        cars.remove(cop)
                police_cars.clear()

    if in_vehicle and current_car:
        current_car.update_player(keys)
        player_x, player_y = current_car.x, current_car.y
    else:
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx or dy:
            length = math.hypot(dx, dy)
            nx = max(20, min(WORLD_SIZE - 20, player_x + (dx / length) * 4.2))
            ny = max(20, min(WORLD_SIZE - 20, player_y + (dy / length) * 4.2))
            if not any(pygame.Rect(nx - 8, ny - 8, 16, 16).colliderect(b["rect"]) for b in buildings):
                player_x, player_y = nx, ny

    for cop in police_cars:
        cop.update_police(player_x, player_y, wanted_level)

    for ped in pedestrians:
        ped.update()
        if in_vehicle and current_car and abs(current_car.speed) > 3.5 and math.hypot(ped.x - current_car.x, ped.y - current_car.y) < 26:
            ped.respawn()
            cash += 50
            add_wanted()

    player_rect = pygame.Rect(player_x - 16, player_y - 16, 32, 32)
    for pickup in cash_pickups[:]:
        if player_rect.colliderect(pickup):
            cash += 100
            cash_pickups.remove(pickup)
            cash_pickups.append(pygame.Rect(random.randint(100, WORLD_SIZE - 100), random.randint(100, WORLD_SIZE - 100), 18, 18))

    cam_x, cam_y = player_x - WIDTH // 2, player_y - HEIGHT // 2
    screen.fill(C_ASPHALT)

    for g in range(0, WORLD_SIZE + 1, BLOCK_SIZE):
        pygame.draw.line(screen, C_LINE, (g - cam_x, -cam_y), (g - cam_x, WORLD_SIZE - cam_y), 2)
        pygame.draw.line(screen, C_LINE, (-cam_x, g - cam_y), (WORLD_SIZE - cam_x, g - cam_y), 2)

    for pickup in cash_pickups:
        rx, ry = pickup.x - cam_x, pickup.y - cam_y
        if -30 < rx < WIDTH + 30 and -30 < ry < HEIGHT + 30:
            pygame.draw.rect(screen, (50, 220, 90), (rx, ry, 18, 18), border_radius=4)
            pygame.draw.rect(screen, C_WHITE, (rx, ry, 18, 18), 1, border_radius=4)

    for ped in pedestrians:
        ped.draw(screen, cam_x, cam_y)
    for car in cars:
        car.draw(screen, cam_x, cam_y)

    if not in_vehicle:
        px, py = int(player_x - cam_x), int(player_y - cam_y)
        pygame.draw.circle(screen, C_WHITE, (px, py), 9)
        pygame.draw.circle(screen, C_NEON_PINK, (px, py), 6)

        for b in buildings:
        bx = b["rect"].x - cam_x
        by = b["rect"].y - cam_y
        if bx + b["rect"].width < -50 or bx > WIDTH + 50 or by + b["rect"].height < -50 or by > HEIGHT + 50:
            continue
        pygame.draw.rect(screen, C_SIDEWALK, (bx - 16, by - 16, b["rect"].width + 32, b["rect"].height + 32), border_radius=6)
        pygame.draw.rect(screen, b["color"], (bx, by, b["rect"].width, b["rect"].height), border_radius=4)
        pygame.draw.rect(screen, b["accent"], (bx + 6, by + 6, b["rect"].width - 12, b["rect"].height - 12), 3, border_radius=3)

    pygame.draw.rect(screen, (15, 15, 22), (0, 0, WIDTH, 44))
    screen.blit(font_ui.render(f"${cash:07d}", True, (80, 235, 110)), (20, 10))
    stars_str = "★ " * wanted_level + "☆ " * (5 - wanted_level)
    screen.blit(font_stars.render(stars_str.strip(), True, C_GOLD if wanted_level > 0 else (110, 110, 120)), (WIDTH - 190, 7))
    screen.blit(font_small.render("WASD/Arrows: Move/Drive | SPACE: Drift | E: Enter/Exit Car | C: Clear Wanted", True, C_WHITE), (210, 13))
    pygame.display.flip()

pygame.quit()
sys.exit()
