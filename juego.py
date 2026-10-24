"""
🐱 MICHI JUMP - Juego de plataformas en Python (Pygame)

Instalación:   pip install pygame
Ejecución:     python gato_plataformas.py

Controles:
  ← → / A D ........ moverse
  ESPACIO / ↑ / W .. saltar
  Enter ............ reiniciar (en Game Over / Victoria)
  ESC .............. salir

Objetivo: recoge pescados, evita perros y pinchos, salta sobre los perros
para eliminarlos y llega a la bandera de cada nivel. Tienes 3 vidas.

Objetos:
  ⭐ Estrella ....... 3 segundos de inmunidad (ignoras perros y pinchos
                      y puedes eliminar perros al tocarlos). No te salva
                      de caer al vacío.
  🚩 Checkpoint ..... al tocarlo se guarda tu punto de reaparición.
"""
import sys
import math
import pygame

pygame.init()
W, H = 800, 500
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Michi Jump")
clock = pygame.time.Clock()
FPS = 60
SHIELD_TIME = 3 * FPS   # 3 segundos de inmunidad

font = pygame.font.SysFont("arial", 22, bold=True)
big = pygame.font.SysFont("arial", 56, bold=True)
mid = pygame.font.SysFont("arial", 28, bold=True)

# ---------------------------------------------------------------- NIVELES
# platforms: (x, y, w, h)   enemies: (x_izq, x_der, y_suelo, velocidad)
# fish: (x, y)   spikes: (x, y_suelo)   goal: (x, y_suelo)
LEVELS = [
    {   # NIVEL 1 - Fácil
        "width": 2400,
        "sky": ((135, 206, 250), (224, 247, 255)),
        "platforms": [
            (0, 460, 650, 40), (800, 460, 600, 40), (1550, 460, 850, 40),
            (300, 360, 120, 16), (950, 350, 140, 16),
            (1150, 270, 120, 16), (1700, 360, 140, 16),
        ],
        "enemies": [(830, 1370, 460, 1.5), (1700, 2100, 460, 2.0)],
        "fish": [(350, 320), (500, 420), (1000, 310), (1190, 230),
                 (1100, 420), (1750, 320), (2100, 420)],
        "spikes": [(1300, 460)],
        "goal": (2300, 460),
        "powerups": [(1230, 430)],
        "checkpoints": [(1580, 460)],
    },
    {   # NIVEL 2 - Medio
        "width": 3000,
        "sky": ((255, 183, 120), (255, 236, 200)),
        "platforms": [
            (0, 460, 500, 40), (650, 460, 400, 40), (1200, 460, 350, 40),
            (1700, 460, 500, 40), (2350, 460, 650, 40),
            (520, 370, 110, 16), (1060, 360, 120, 16),
            (1560, 360, 110, 16), (900, 280, 100, 16),
            (2200, 370, 130, 16), (1850, 300, 120, 16),
        ],
        "enemies": [(670, 1030, 460, 2.0), (1300, 1530, 460, 2.2),
                    (1720, 2180, 460, 2.5), (2400, 2900, 460, 2.5)],
        "fish": [(560, 330), (940, 240), (1100, 320), (1400, 420),
                 (1600, 320), (1890, 260), (2250, 330), (2700, 420)],
        "spikes": [(450, 460), (850, 460), (1450, 460), (2000, 460), (2600, 460)],
        "goal": (2900, 460),
        "powerups": [(780, 430), (1900, 430)],
        "checkpoints": [(1210, 460), (2360, 460)],
    },
    {   # NIVEL 3 - Difícil
        "width": 3600,
        "sky": ((60, 40, 110), (160, 110, 190)),
        "platforms": [
            (0, 460, 380, 40), (520, 460, 280, 40), (950, 460, 250, 40),
            (1650, 460, 300, 40), (2300, 460, 280, 40), (2900, 460, 700, 40),
            (400, 380, 90, 16), (820, 340, 90, 16), (1220, 380, 90, 16),
            (1380, 300, 90, 16), (1530, 380, 90, 16), (1990, 380, 90, 16),
            (2130, 300, 90, 16), (2620, 380, 90, 16), (2760, 310, 90, 16),
        ],
        "enemies": [(540, 780, 460, 2.6), (960, 1190, 460, 2.8),
                    (1760, 1940, 460, 3.0), (2400, 2570, 460, 3.0),
                    (3100, 3500, 460, 3.2)],
        "fish": [(430, 340), (850, 300), (1250, 340), (1410, 260),
                 (1560, 340), (2020, 340), (2160, 260), (2650, 340),
                 (2790, 270), (3100, 420)],
        "spikes": [(700, 460), (1100, 460), (1800, 460), (2450, 460),
                   (3050, 460), (3250, 460)],
        "goal": (3500, 460),
        "powerups": [(1000, 430), (2400, 430), (3000, 430)],
        "checkpoints": [(1660, 460), (2310, 460), (2910, 460)],
    },
]


# ---------------------------------------------------------------- CLASES
class Player:
    W, H = 36, 28

    def __init__(self, x, y):
        self.start = (x, y)
        self.rect = pygame.Rect(x, y, self.W, self.H)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1
        self.invuln = 0
        self.shield = 0
        self.anim = 0

    def respawn(self):
        self.rect.topleft = self.start
        self.vx = self.vy = 0
        self.invuln = 120
        self.shield = 0

    def protected(self):
        return self.invuln > 0 or self.shield > 0

    def update(self, keys, platforms):
        accel = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            accel -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            accel += 1
        self.vx = accel * 5
        if accel:
            self.facing = accel
            self.anim += 1

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) \
                and self.on_ground:
            self.vy = -13.5
            self.on_ground = False

        self.vy = min(self.vy + 0.6, 15)

        # Movimiento horizontal
        self.rect.x += int(self.vx)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vx > 0:
                    self.rect.right = p.left
                elif self.vx < 0:
                    self.rect.left = p.right
        if self.rect.left < 0:
            self.rect.left = 0

        # Movimiento vertical
        self.rect.y += int(self.vy)
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vy > 0:
                    self.rect.bottom = p.top
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = p.bottom
                self.vy = 0

        if self.invuln > 0:
            self.invuln -= 1
        if self.shield > 0:
            self.shield -= 1

    def draw(self, surf, cam):
        r = self.rect.move(-cam, 0)
        # burbuja de inmunidad (parpadea en el último segundo)
        if self.shield > 0 and (self.shield > 60 or (self.shield // 5) % 2 == 0):
            bubble = pygame.Surface((70, 70), pygame.SRCALPHA)
            pygame.draw.circle(bubble, (80, 200, 255, 90), (35, 35), 34)
            pygame.draw.circle(bubble, (200, 245, 255, 230), (35, 35), 34, 3)
            surf.blit(bubble, (r.centerx - 35, r.centery - 35))
        if self.invuln > 0 and (self.invuln // 5) % 2 == 0:
            return  # parpadeo
        d = self.facing
        orange, dark = (240, 150, 60), (200, 110, 30)
        # cola
        wag = (self.anim // 6) % 2 * 4
        tail = [(r.centerx - 16 * d, r.centery + 4),
                (r.centerx - 26 * d, r.centery - 4 - wag),
                (r.centerx - 24 * d, r.centery - 16 - wag)]
        pygame.draw.lines(surf, dark, False, tail, 5)
        # patas
        step = 3 if (self.anim // 5) % 2 and self.on_ground else 0
        pygame.draw.rect(surf, dark, (r.x + 5, r.bottom - 8, 8, 8 - step))
        pygame.draw.rect(surf, dark, (r.right - 13, r.bottom - 8, 8, 8 + step - 3 if step else 8))
        # cuerpo
        pygame.draw.ellipse(surf, orange, (r.x, r.y + 6, r.w, r.h - 6))
        # rayas
        for i in (10, 18, 26):
            pygame.draw.line(surf, dark, (r.x + i, r.y + 8), (r.x + i, r.y + 14), 2)
        # cabeza
        hx = r.centerx + 10 * d
        hy = r.y + 8
        pygame.draw.circle(surf, orange, (hx, hy), 11)
        # orejas
        for s in (-1, 1):
            ex = hx + 6 * s
            pygame.draw.polygon(surf, orange,
                                [(ex - 4, hy - 7), (ex + 4, hy - 7), (ex + 2 * s, hy - 18)])
            pygame.draw.polygon(surf, (255, 170, 170),
                                [(ex - 2, hy - 8), (ex + 2, hy - 8), (ex + 1 * s, hy - 14)])
        # ojos, nariz, bigotes
        pygame.draw.circle(surf, (30, 30, 30), (hx + 4 * d - 3, hy - 1), 2)
        pygame.draw.circle(surf, (30, 30, 30), (hx + 4 * d + 3, hy - 1), 2)
        pygame.draw.circle(surf, (255, 120, 140), (hx + 6 * d, hy + 3), 2)
        for s in (-1, 1):
            pygame.draw.line(surf, (60, 40, 20), (hx + 5 * d, hy + 4),
                             (hx + 5 * d + 11 * d, hy + 4 + 3 * s), 1)


class Enemy:
    def __init__(self, x1, x2, ground, speed):
        self.rect = pygame.Rect(x1, ground - 30, 38, 30)
        self.x1, self.x2 = x1, x2
        self.dir = 1
        self.speed = speed
        self.alive = True
        self.t = 0

    def update(self):
        self.rect.x += int(self.dir * self.speed) if self.speed >= 1 else self.dir
        self.t += 1
        if self.rect.right >= self.x2:
            self.dir = -1
        elif self.rect.left <= self.x1:
            self.dir = 1

    def draw(self, surf, cam):
        r = self.rect.move(-cam, 0)
        col, dark = (140, 100, 70), (90, 60, 40)
        pygame.draw.ellipse(surf, col, (r.x, r.y + 6, r.w, r.h - 6))
        hx = r.centerx + 12 * self.dir
        pygame.draw.circle(surf, col, (hx, r.y + 8), 11)
        pygame.draw.ellipse(surf, dark, (hx - 15 if self.dir < 0 else hx + 3, r.y + 2, 11, 16))
        pygame.draw.circle(surf, (255, 255, 255), (hx + 4 * self.dir, r.y + 6), 4)
        pygame.draw.circle(surf, (200, 0, 0), (hx + 5 * self.dir, r.y + 6), 2)
        pygame.draw.circle(surf, (20, 20, 20), (hx + 14 * self.dir, r.y + 12), 3)
        off = 3 if (self.t // 8) % 2 else 0
        pygame.draw.rect(surf, dark, (r.x + 4, r.bottom - 6, 7, 6 - off))
        pygame.draw.rect(surf, dark, (r.right - 11, r.bottom - 6, 7, 3 + off))


class PowerUp:
    """Estrella que da inmunidad durante 3 segundos."""

    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 14, y - 14, 28, 28)
        self.base_y = y

    def draw(self, surf, cam, t):
        cx = self.rect.centerx - cam
        if cx < -40 or cx > W + 40:
            return
        cy = self.base_y + int(math.sin(t / 12) * 4)
        glow = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 255, 150, 70), (25, 25), 22)
        surf.blit(glow, (cx - 25, cy - 25))
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = 13 if i % 2 == 0 else 6
            pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
        pygame.draw.polygon(surf, (255, 215, 60), pts)
        pygame.draw.polygon(surf, (255, 255, 200), pts, 2)


class Checkpoint:
    """Bandera que guarda el punto de reaparición."""

    def __init__(self, x, ground):
        self.pole = pygame.Rect(x, ground - 64, 8, 64)
        self.trigger = pygame.Rect(x - 20, ground - 80, 48, 80)
        self.spawn = (x, ground - Player.H - 1)
        self.active = False

    def draw(self, surf, cam):
        p = self.pole.move(-cam, 0)
        if p.right < -40 or p.x > W + 40:
            return
        pygame.draw.rect(surf, (210, 210, 210), p)
        col = (60, 220, 90) if self.active else (150, 150, 150)
        pygame.draw.polygon(surf, col, [(p.right, p.y), (p.right + 32, p.y + 12),
                                        (p.right, p.y + 24)])
        ball = (255, 255, 120) if self.active else (110, 110, 110)
        pygame.draw.circle(surf, ball, (p.x + 4, p.y - 4), 6)


# ---------------------------------------------------------------- FUNCIONES
def load_level(i):
    d = LEVELS[i]
    platforms = [pygame.Rect(*p) for p in d["platforms"]]
    enemies = [Enemy(*e) for e in d["enemies"]]
    fish = [pygame.Rect(x - 10, y - 8, 20, 16) for x, y in d["fish"]]
    spikes = [pygame.Rect(x, y - 18, 30, 18) for x, y in d["spikes"]]
    gx, gy = d["goal"]
    goal = pygame.Rect(gx, gy - 90, 40, 90)
    powerups = [PowerUp(x, y) for x, y in d["powerups"]]
    checkpoints = [Checkpoint(x, y) for x, y in d["checkpoints"]]
    return d, platforms, enemies, fish, spikes, goal, powerups, checkpoints


def draw_sky(level):
    top, bot = level["sky"]
    for y in range(0, H, 4):
        t = y / H
        c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        pygame.draw.rect(screen, c, (0, y, W, 4))


def draw_platform(r, cam, level_idx):
    r = r.move(-cam, 0)
    if r.x > W or r.right < 0:
        return
    base = [(110, 75, 45), (150, 90, 50), (80, 60, 90)][level_idx]
    grass = [(80, 180, 80), (210, 170, 70), (130, 90, 190)][level_idx]
    pygame.draw.rect(screen, base, r)
    pygame.draw.rect(screen, grass, (r.x, r.y, r.w, 8))


def draw_fish(r, cam, t):
    r = r.move(-cam, int(3 * pygame.math.Vector2(0, 1).y * ((t // 10) % 2)))
    pygame.draw.ellipse(screen, (120, 200, 255), r)
    pygame.draw.polygon(screen, (120, 200, 255),
                        [(r.right - 2, r.centery), (r.right + 8, r.y), (r.right + 8, r.bottom)])
    pygame.draw.circle(screen, (0, 0, 0), (r.x + 5, r.centery - 2), 2)


def draw_spike(r, cam):
    r = r.move(-cam, 0)
    for i in range(3):
        x = r.x + i * 10
        pygame.draw.polygon(screen, (190, 190, 200),
                            [(x, r.bottom), (x + 10, r.bottom), (x + 5, r.y)])


def draw_goal(r, cam):
    r = r.move(-cam, 0)
    pygame.draw.rect(screen, (230, 230, 230), (r.x, r.y, 6, r.h))
    pygame.draw.polygon(screen, (255, 70, 90),
                        [(r.x + 6, r.y), (r.x + 40, r.y + 14), (r.x + 6, r.y + 28)])


def draw_heart(x, y, full=True):
    col = (235, 50, 70) if full else (90, 90, 90)
    pygame.draw.circle(screen, col, (x - 6, y), 7)
    pygame.draw.circle(screen, col, (x + 6, y), 7)
    pygame.draw.polygon(screen, col, [(x - 13, y + 3), (x + 13, y + 3), (x, y + 17)])


def center_text(txt, f, y, color=(255, 255, 255)):
    shadow = f.render(txt, True, (0, 0, 0))
    img = f.render(txt, True, color)
    screen.blit(shadow, (W // 2 - img.get_width() // 2 + 2, y + 2))
    screen.blit(img, (W // 2 - img.get_width() // 2, y))


# ---------------------------------------------------------------- JUEGO
def main():
    level_idx = 0
    lives = 3
    score = 0
    state = "play"          # play | gameover | win
    banner = 150            # temporizador del título del nivel
    t = 0

    level, platforms, enemies, fish, spikes, goal, powerups, checkpoints = load_level(level_idx)
    player = Player(60, 400)
    player.invuln = 60
    msg, msg_t = "", 0

    def hurt():
        nonlocal lives, state
        lives -= 1
        if lives <= 0:
            state = "gameover"
        else:
            player.respawn()

    while True:
        clock.tick(FPS)
        t += 1
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if e.key == pygame.K_RETURN and state in ("gameover", "win"):
                    return main()

        keys = pygame.key.get_pressed()

        # ---------------- Lógica
        if state == "play":
            player.update(keys, platforms)
            for en in enemies:
                if en.alive:
                    en.update()

            # Pescados
            for f in fish[:]:
                if player.rect.colliderect(f):
                    fish.remove(f)
                    score += 10

            # Estrellas de inmunidad
            for pu in powerups[:]:
                if player.rect.colliderect(pu.rect):
                    powerups.remove(pu)
                    player.shield = SHIELD_TIME
                    score += 20

            # Puntos de reaparición
            for cp in checkpoints:
                if not cp.active and player.rect.colliderect(cp.trigger):
                    cp.active = True
                    player.start = cp.spawn
                    msg, msg_t = "¡Punto de reaparición guardado!", 120

            # Enemigos
            for en in enemies:
                if en.alive and player.rect.colliderect(en.rect):
                    if player.vy > 0 and player.rect.bottom - int(player.vy) <= en.rect.top + 8:
                        en.alive = False
                        player.vy = -9
                        score += 50
                    elif player.shield > 0:
                        en.alive = False      # con inmunidad eliminas al perro
                        score += 50
                    elif player.invuln == 0:
                        hurt()
                        break

            # Pinchos
            if state == "play" and not player.protected():
                for s in spikes:
                    if player.rect.colliderect(s.inflate(-6, -4)):
                        hurt()
                        break

            # Caída al vacío
            if state == "play" and player.rect.top > H + 80:
                hurt()

            # Meta
            if state == "play" and player.rect.colliderect(goal):
                score += 100
                level_idx += 1
                if level_idx >= len(LEVELS):
                    state = "win"
                else:
                    level, platforms, enemies, fish, spikes, goal, powerups, checkpoints = load_level(level_idx)
                    player = Player(60, 400)
                    player.invuln = 60
                    banner = 150

        # ---------------- Dibujo
        cam = max(0, min(player.rect.centerx - W // 2, level["width"] - W))
        draw_sky(level)
        # nubes con parallax
        for i in range(8):
            cx = (i * 330 - cam * 0.3) % (W + 300) - 150
            pygame.draw.ellipse(screen, (255, 255, 255, 90), (cx, 60 + (i % 3) * 45, 120, 36))

        for p in platforms:
            draw_platform(p, cam, level_idx)
        for s in spikes:
            draw_spike(s, cam)
        for f in fish:
            draw_fish(f, cam, t)
        for cp in checkpoints:
            cp.draw(screen, cam)
        for pu in powerups:
            pu.draw(screen, cam, t)
        draw_goal(goal, cam)
        for en in enemies:
            if en.alive:
                en.draw(screen, cam)
        player.draw(screen, cam)

        # HUD
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, W, 38))
        for i in range(3):
            draw_heart(26 + i * 34, 12, i < lives)
        screen.blit(font.render(f"Nivel {level_idx + 1}/3", True, (255, 255, 255)), (W // 2 - 45, 7))
        screen.blit(font.render(f"Puntos: {score}", True, (255, 220, 100)), (W - 150, 7))
        if player.shield > 0:
            pygame.draw.rect(screen, (40, 40, 40), (10, 46, 124, 14))
            pygame.draw.rect(screen, (80, 200, 255),
                             (12, 48, int(120 * player.shield / SHIELD_TIME), 10))
            screen.blit(font.render(f"Inmune {player.shield / FPS:.1f}s", True, (255, 255, 255)),
                        (142, 41))

        if banner > 0 and state == "play":
            banner -= 1
            center_text(f"NIVEL {level_idx + 1}", big, 160)

        if msg_t > 0 and state == "play":
            msg_t -= 1
            center_text(msg, mid, 100, (120, 255, 150))

        if state == "gameover":
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 170))
            screen.blit(ov, (0, 0))
            center_text("GAME OVER", big, 150, (255, 90, 90))
            center_text(f"Puntos: {score}", mid, 240)
            center_text("Pulsa ENTER para reintentar", mid, 300)
        elif state == "win":
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 150))
            screen.blit(ov, (0, 0))
            center_text("¡GANASTE! 🐱", big, 140, (255, 220, 100))
            center_text(f"Puntos finales: {score + lives * 100} (vidas x100 incluidas)", mid, 240)
            center_text("Pulsa ENTER para jugar de nuevo", mid, 300)

        pygame.display.flip()


if __name__ == "__main__":
    main()