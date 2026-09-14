#!/usr/bin/env python3
"""Quark Sweep — neon minesweeper arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/QUARK_SWEEP_ElbowOS.mp4")
TITLE, HANDLE = "QUARK SWEEP", "x.com/ElbowOS"

BG, WELL = (8, 12, 28), (14, 22, 48)
INK, GOLD, WHITE = (28, 48, 92), (255, 214, 90), (236, 246, 255)
CYAN, MAG, LIME, ROSE = (40, 230, 255), (255, 70, 180), (160, 255, 90), (255, 90, 130)
NUMC = [WHITE, (80, 210, 255), (90, 255, 160), (255, 90, 140),
        (180, 130, 255), (255, 180, 60), (255, 70, 90), CYAN, MAG]


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("DejaVu Sans", 64, bold=True)
        self.font = pygame.font.SysFont("DejaVu Sans", 42, bold=True)
        self.font_sm = pygame.font.SysFont("DejaVu Sans", 26)
        self.font_n = pygame.font.SysFont("DejaVu Sans", 48, bold=True)
        self.clock = pygame.time.Clock()
        self.cols, self.rows, self.nmines = 8, 10, 12
        self.cs = 100
        self.ox = (W - self.cols * self.cs) // 2
        self.oy = 280
        self.score = self.t = self.flash = self.won = 0
        self.cursor = [0, 0]
        self.sparks, self.stars = [], []
        for _ in range(55):
            self.stars.append([random.randint(0, W), random.randint(0, H),
                               random.uniform(0.3, 1.6), random.choice([CYAN, MAG, GOLD, LIME])])
        self.reset()

    def reset(self):
        self.mines = set()
        while len(self.mines) < self.nmines:
            self.mines.add((random.randrange(self.cols), random.randrange(self.rows)))
        self.open = set()
        self.flags = set()
        self.dead = False
        self.won = 0
        self.score = max(0, self.score)
        self.ripple = []

    def adj(self, x, y):
        return [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                if (dx or dy) and 0 <= x + dx < self.cols and 0 <= y + dy < self.rows]

    def count(self, x, y):
        return sum(1 for n in self.adj(x, y) if n in self.mines)

    def reveal(self, x, y):
        if (x, y) in self.flags or (x, y) in self.open or self.dead:
            return
        if (x, y) in self.mines:
            self.dead = True
            self.flash = 14
            self.burst(self.cx(x), self.cy(y), ROSE, 22)
            return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in self.open or (cx, cy) in self.mines:
                continue
            self.open.add((cx, cy))
            self.score += 12
            self.ripple.append([self.cx(cx), self.cy(cy), 6, CYAN])
            if self.count(cx, cy) == 0:
                stack.extend(self.adj(cx, cy))
        if len(self.open) == self.cols * self.rows - self.nmines:
            self.won = 1
            self.score += 400
            self.flash = 12

    def toggle_flag(self, x, y):
        if (x, y) in self.open or self.dead:
            return
        if (x, y) in self.flags:
            self.flags.remove((x, y))
        else:
            self.flags.add((x, y))
            self.score += 4 if (x, y) in self.mines else 0
            self.burst(self.cx(x), self.cy(y), GOLD, 6)

    def cx(self, x):
        return self.ox + x * self.cs + self.cs // 2

    def cy(self, y):
        return self.oy + y * self.cs + self.cs // 2

    def burst(self, x, y, col, n=8):
        for _ in range(n):
            a = random.uniform(0, 6.28)
            sp = random.uniform(2, 11)
            self.sparks.append([x, y, math.cos(a) * sp, math.sin(a) * sp, 22, col])

    def autoplay(self):
        if self.dead or self.won:
            if self.t % 28 == 0:
                self.reset()
            return
        changed = False
        for (x, y) in list(self.open):
            n = self.count(x, y)
            if n == 0:
                continue
            neigh = self.adj(x, y)
            hidden = [c for c in neigh if c not in self.open]
            flagged = [c for c in hidden if c in self.flags]
            unknown = [c for c in hidden if c not in self.flags]
            if n == len(hidden) and unknown:
                self.toggle_flag(*unknown[0])
                changed = True
                break
            if n == len(flagged) and unknown:
                self.reveal(*unknown[0])
                changed = True
                break
        if changed:
            return
        hidden = [(x, y) for x in range(self.cols) for y in range(self.rows)
                  if (x, y) not in self.open and (x, y) not in self.flags]
        if not hidden:
            return
        safe = [c for c in hidden if c not in self.mines]
        pool = safe if safe and random.random() < 0.82 else hidden
        near = [c for c in pool if abs(c[0] - self.cursor[0]) + abs(c[1] - self.cursor[1]) <= 3]
        pick = random.choice(near or pool)
        self.cursor = list(pick)
        if pick in self.mines and random.random() < 0.7:
            self.toggle_flag(*pick)
        else:
            self.reveal(*pick)

    def tick(self):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        for s in self.sparks:
            s[0] += s[2]
            s[1] += s[3]
            s[3] += 0.18
            s[4] -= 1
        self.sparks = [s for s in self.sparks if s[4] > 0]
        for r in self.ripple:
            r[2] += 4
        self.ripple = [r for r in self.ripple if r[2] < 90]
        for e in self.stars:
            e[1] -= e[2]
            if e[1] < -6:
                e[1] = H + 6
                e[0] = random.randint(0, W)

    def draw_cell(self, surf, x, y):
        r = pygame.Rect(self.ox + x * self.cs + 5, self.oy + y * self.cs + 5, self.cs - 10, self.cs - 10)
        pulse = 10 + int(8 * math.sin(self.t * 0.12 + x * 0.7 + y * 0.5))
        if (x, y) in self.open:
            pygame.draw.rect(surf, (18, 28, 58), r, border_radius=14)
            pygame.draw.rect(surf, (50, 80, 140), r, 2, border_radius=14)
            if (x, y) in self.mines:
                pygame.draw.circle(surf, ROSE, r.center, 22)
                pygame.draw.circle(surf, WHITE, r.center, 8)
            else:
                n = self.count(x, y)
                if n:
                    lab = self.font_n.render(str(n), True, NUMC[n])
                    surf.blit(lab, lab.get_rect(center=r.center))
        else:
            col = (24 + pulse, 36 + pulse // 2, 78 + pulse)
            pygame.draw.rect(surf, col, r, border_radius=14)
            hi = pygame.Rect(r.x + 10, r.y + 8, r.w // 2, 10)
            pygame.draw.rect(surf, (90, 140, 220), hi, border_radius=5)
            pygame.draw.rect(surf, CYAN if (x, y) != tuple(self.cursor) else GOLD, r, 3, border_radius=14)
            if (x, y) in self.flags:
                pts = [(r.centerx - 8, r.bottom - 18), (r.centerx - 8, r.top + 16),
                       (r.centerx + 22, r.centery - 6), (r.centerx - 8, r.centery + 8)]
                pygame.draw.polygon(surf, MAG, pts)
                pygame.draw.line(surf, WHITE, (r.centerx - 8, r.top + 16), (r.centerx - 8, r.bottom - 16), 4)
        if (x, y) == tuple(self.cursor):
            pygame.draw.rect(surf, GOLD, r.inflate(8, 8), 3, border_radius=16)

    def draw(self, surf):
        surf.fill(BG)
        for e in self.stars:
            pygame.draw.circle(surf, e[3], (int(e[0]), int(e[1])), 2)
        well = pygame.Rect(self.ox - 18, self.oy - 18, self.cols * self.cs + 36, self.rows * self.cs + 36)
        pygame.draw.rect(surf, WELL, well, border_radius=22)
        pygame.draw.rect(surf, CYAN, well, 4, border_radius=22)
        for y in range(self.rows):
            for x in range(self.cols):
                self.draw_cell(surf, x, y)
        for r in self.ripple:
            pygame.draw.circle(surf, CYAN, (int(r[0]), int(r[1])), int(r[2]), 2)
        for s in self.sparks:
            pygame.draw.circle(surf, s[5], (int(s[0]), int(s[1])), max(2, s[4] // 4))
        if self.flash:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 80, 160, 36) if self.dead else (80, 255, 200, 32))
            surf.blit(ov, (0, 0))
        title = self.font_lg.render(TITLE, True, CYAN)
        surf.blit(title, title.get_rect(center=(W // 2, 82)))
        sub = self.font_sm.render(HANDLE, True, MAG)
        surf.blit(sub, sub.get_rect(center=(W // 2, 142)))
        left = self.nmines - len(self.flags)
        sc = self.font.render(f"SCORE  {self.score}", True, WHITE)
        mn = self.font.render(f"CORES  {max(0, left)}", True, GOLD)
        surf.blit(sc, sc.get_rect(center=(W // 2, H - 168)))
        surf.blit(mn, mn.get_rect(center=(W // 2, H - 108)))
        hint = self.font_sm.render("click reveal   right-click flag   arrows move", True, (120, 160, 210))
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 52)))

    def cell_at(self, mx, my):
        if not (self.ox <= mx < self.ox + self.cols * self.cs and
                self.oy <= my < self.oy + self.rows * self.cs):
            return None
        return ((mx - self.ox) // self.cs, (my - self.oy) // self.cs)

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_LEFT, pygame.K_a):
                        self.cursor[0] = max(0, self.cursor[0] - 1)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        self.cursor[0] = min(self.cols - 1, self.cursor[0] + 1)
                    elif ev.key in (pygame.K_UP, pygame.K_w):
                        self.cursor[1] = max(0, self.cursor[1] - 1)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        self.cursor[1] = min(self.rows - 1, self.cursor[1] + 1)
                    elif ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.reveal(*self.cursor)
                    elif ev.key in (pygame.K_f, pygame.K_LSHIFT):
                        self.toggle_flag(*self.cursor)
                    elif ev.key == pygame.K_r:
                        self.reset()
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    cell = self.cell_at(*ev.pos)
                    if cell:
                        self.cursor = list(cell)
                        if ev.button == 1:
                            self.reveal(*cell)
                        elif ev.button == 3:
                            self.toggle_flag(*cell)
            self.tick()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                if i % 5 == 0:
                    self.autoplay()
                self.tick()
                self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames}", flush=True)
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
