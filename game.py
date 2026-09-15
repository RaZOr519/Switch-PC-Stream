import sys
import random
import math
import pygame

# Initialize Pygame & Joystick
pygame.init()
pygame.joystick.init()

# Setup 1280x720 Display (Native Switch Lite resolution)
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Switch Lite Streaming Demo Game - Space Defender 60FPS")
clock = pygame.time.Clock()

# Colors
BLACK = (10, 15, 26)
WHITE = (255, 255, 255)
CYAN = (0, 240, 255)
MAGENTA = (255, 0, 128)
YELLOW = (255, 220, 0)
GREEN = (50, 255, 100)
RED = (255, 60, 60)

# Check for Xbox Controller (including Virtual Controller from server.py)
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"[GAME] Controller detected: {joystick.get_name()}")
else:
    print("[GAME] No controller detected at launch. Plug in or start server.py virtual controller.")

class Player:
    def __init__(self):
        self.x = WIDTH // 4
        self.y = HEIGHT // 2
        self.speed = 8
        self.radius = 20
        self.health = 100
        self.score = 0
        self.cooldown = 0

    def draw(self, surface):
        # Draw Neon Fighter Ship
        pts = [
            (self.x + 25, self.y),
            (self.x - 20, self.y - 15),
            (self.x - 10, self.y),
            (self.x - 20, self.y + 15)
        ]
        pygame.draw.polygon(surface, CYAN, pts)
        pygame.draw.polygon(surface, WHITE, pts, 2)
        # Thruster glow
        pygame.draw.circle(surface, MAGENTA, (int(self.x - 18), int(self.y)), random.randint(4, 8))

    def update(self, keys, js):
        dx, dy = 0, 0
        
        # Keyboard controls
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1

        # Xbox / Switch Controller controls
        if js:
            try:
                jx = js.get_axis(0)
                jy = js.get_axis(1)
                if abs(jx) > 0.15: dx += jx
                if abs(jy) > 0.15: dy += jy
                
                # D-Pad
                hat = js.get_hat(0) if js.get_numhats() > 0 else (0, 0)
                dx += hat[0]
                dy -= hat[1]
            except Exception:
                pass

        self.x += dx * self.speed
        self.y += dy * self.speed

        # Clamp bounds
        self.x = max(30, min(WIDTH - 50, self.x))
        self.y = max(30, min(HEIGHT - 30, self.y))

        if self.cooldown > 0:
            self.cooldown -= 1

class Laser:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 18

    def update(self):
        self.x += self.speed

    def draw(self, surface):
        pygame.draw.line(surface, YELLOW, (self.x, self.y), (self.x + 16, self.y), 4)

class Enemy:
    def __init__(self):
        self.x = WIDTH + random.randint(20, 100)
        self.y = random.randint(50, HEIGHT - 50)
        self.speed = random.randint(4, 9)
        self.radius = random.randint(15, 25)
        self.color = RED

    def update(self):
        self.x -= self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)
        self.life = random.randint(10, 25)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), max(1, self.life // 4))

def main():
    player = Player()
    lasers = []
    enemies = []
    particles = []
    
    # Background Starfield
    stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)) for _ in range(80)]

    font_large = pygame.font.SysFont("Arial", 28, bold=True)
    font_small = pygame.font.SysFont("Arial", 18)

    running = True
    while running:
        clock.tick(60) # Target 60 FPS
        
        # Check hotplugged joystick
        global joystick
        if not joystick and pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            print(f"[GAME] Controller connected: {joystick.get_name()}")

        keys = pygame.key.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Fire laser (Keyboard Space or Controller Button A / Trigger)
        shoot = keys[pygame.K_SPACE]
        if joystick:
            try:
                if joystick.get_button(0) or joystick.get_button(7) > 0.3: # Button A / RT
                    shoot = True
            except Exception:
                pass

        if shoot and player.cooldown == 0:
            lasers.append(Laser(player.x + 25, player.y))
            player.cooldown = 8

        # Update Game Entities
        player.update(keys, joystick)

        for l in lasers[:]:
            l.update()
            if l.x > WIDTH:
                lasers.remove(l)

        # Spawn Enemies
        if random.random() < 0.06:
            enemies.append(Enemy())

        for e in enemies[:]:
            e.update()
            if e.x < -30:
                enemies.remove(e)
                player.score = max(0, player.score - 50)
                continue

            # Check collision with lasers
            for l in lasers[:]:
                if math.hypot(e.x - l.x, e.y - l.y) < e.radius + 5:
                    # Explode
                    for _ in range(12):
                        particles.append(Particle(e.x, e.y, MAGENTA))
                    if e in enemies: enemies.remove(e)
                    if l in lasers: lasers.remove(l)
                    player.score += 100
                    break

            # Check collision with player
            if math.hypot(e.x - player.x, e.y - player.y) < e.radius + player.radius:
                for _ in range(20):
                    particles.append(Particle(player.x, player.y, RED))
                if e in enemies: enemies.remove(e)
                player.health -= 15
                if player.health <= 0:
                    player.health = 100
                    player.score = 0

        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        # RENDER SCREEN
        screen.fill(BLACK)

        # Draw Starfield
        for i, (sx, sy, speed) in enumerate(stars):
            sx -= speed * 2
            if sx < 0: sx = WIDTH
            stars[i] = (sx, sy, speed)
            pygame.draw.circle(screen, (180, 200, 255), (int(sx), int(sy)), speed)

        # Draw Entities
        for p in particles: p.draw(screen)
        for l in lasers: l.draw(screen)
        for e in enemies: e.draw(screen)
        player.draw(screen)

        # HUD OVERLAY ON PC GAME SCREEN
        # Header Bar
        pygame.draw.rect(screen, (20, 30, 50), (0, 0, WIDTH, 45))
        pygame.draw.line(screen, CYAN, (0, 45), (WIDTH, 45), 2)

        txt_title = font_large.render("SWITCH LITE GAME STREAMING DEMO - 60 FPS", True, CYAN)
        screen.blit(txt_title, (20, 8))

        txt_score = font_large.render(f"SCORE: {player.score}", True, YELLOW)
        screen.blit(txt_score, (WIDTH - 220, 8))

        # Health Bar
        pygame.draw.rect(screen, (60, 60, 60), (20, HEIGHT - 35, 200, 20))
        hp_w = int((player.health / 100.0) * 200)
        pygame.draw.rect(screen, GREEN if player.health > 40 else RED, (20, HEIGHT - 35, hp_w, 20))
        pygame.draw.rect(screen, WHITE, (20, HEIGHT - 35, 200, 20), 2)
        txt_hp = font_small.render(f"HEALTH {player.health}%", True, WHITE)
        screen.blit(txt_hp, (25, HEIGHT - 33))

        txt_ctrl = font_small.render(f"Controller: {'Xbox 360 (Connected)' if joystick else 'Keyboard (WASD+Space)'}", True, GREEN if joystick else YELLOW)
        screen.blit(txt_ctrl, (WIDTH - 320, HEIGHT - 33))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
