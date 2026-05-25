import math
import random
from typing import Tuple

import cv2

try:
    import pygame

    _PYGAME_AVAILABLE = True
except Exception:
    pygame = None
    _PYGAME_AVAILABLE = False


class Particle:
    def __init__(
        self,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (255, 200, 0),
        size: int | None = None,
        speed_multiplier: float = 1.0,
    ):
        self.x = float(x)
        self.y = float(y)

        # allow overriding size for presets
        self.size = size if size is not None else random.randint(2, 6)

        # small random velocity so the trail spreads a bit
        self.vx = random.uniform(-1.5, 1.5) * speed_multiplier
        self.vy = random.uniform(-1.5, 1.5) * speed_multiplier

        # life in frames
        self.life = random.randint(18, 48)
        self.age = 0

        self.color = color

    def update(self):
        # simple physics
        self.x += self.vx
        self.y += self.vy
        # slight gravity-like pull
        self.vy += 0.03

        # gradual slowing
        self.vx *= 0.99
        self.vy *= 0.99

        self.age += 1

    def draw_cv(self, frame):
        alpha = max(0.0, 1.0 - (self.age / max(1, self.life)))
        color = (
            int(self.color[0] * alpha),
            int(self.color[1] * alpha),
            int(self.color[2] * alpha),
        )

        cv2.circle(frame, (int(self.x), int(self.y)), self.size, color, -1)

    def draw_pygame(self, surface, scale_x: float = 1.0, scale_y: float = 1.0):
        """Draw the particle onto a pygame Surface with glow using concentric circles.

        Coordinates are in camera space; scale_x/scale_y convert to pygame window size.
        """
        alpha = max(0.0, 1.0 - (self.age / max(1, self.life)))
        base_r, base_g, base_b = (
            int(self.color[0]),
            int(self.color[1]),
            int(self.color[2]),
        )

        cx = int(self.x * scale_x)
        cy = int(self.y * scale_y)

        # draw 3 concentric circles for glow: outer (faint), mid, core (bright)
        for i, mul in enumerate((2.2, 1.3, 1.0)):
            a = int(255 * alpha * (0.35 if i == 0 else 0.6 if i == 1 else 1.0))
            r = max(0, min(255, int(base_r)))
            g = max(0, min(255, int(base_g)))
            b = max(0, min(255, int(base_b)))
            color = (r, g, b, a)
            radius = max(1, int(self.size * mul * max(scale_x, scale_y)))
            pygame.draw.circle(surface, color, (cx, cy), radius)

    def is_dead(self) -> bool:
        return self.age >= self.life


def spawn_trail(
    particles: list,
    x: int,
    y: int,
    n: int = 2,
    color: Tuple[int, int, int] = (255, 200, 0),
):
    for _ in range(n):
        particles.append(
            Particle(x + random.uniform(-2, 2), y + random.uniform(-2, 2), color)
        )


def spawn_explosion(particles: list, x: int, y: int, color=(255, 80, 80), n: int = 50):
    for _ in range(n):
        p = Particle(
            x + random.uniform(-4, 4),
            y + random.uniform(-4, 4),
            color,
            size=random.randint(3, 7),
            speed_multiplier=random.uniform(2.5, 5.0),
        )
        particles.append(p)


def spawn_aura(particles: list, x: int, y: int, color=(80, 255, 255), n: int = 30):
    for _ in range(n):
        p = Particle(
            x + random.uniform(-12, 12),
            y + random.uniform(-12, 12),
            color,
            size=random.randint(3, 8),
            speed_multiplier=random.uniform(0.2, 1.0),
        )
        particles.append(p)


def spawn_spark(particles: list, x: int, y: int, color=(255, 255, 50), n: int = 20):
    for _ in range(n):
        p = Particle(
            x + random.uniform(-3, 3),
            y + random.uniform(-3, 3),
            color,
            size=random.randint(1, 3),
            speed_multiplier=random.uniform(2.0, 4.0),
        )
        particles.append(p)


def spawn_orb(particles: list, x: int, y: int, color=(200, 40, 200), n: int = 40):
    # spawn particles in a circular orbit-ish outward pattern
    for i in range(n):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(2, 18)
        px = x + math.cos(angle) * dist
        py = y + math.sin(angle) * dist
        p = Particle(
            px,
            py,
            color,
            size=random.randint(2, 6),
            speed_multiplier=random.uniform(0.3, 1.2),
        )
        particles.append(p)


class LineParticle:
    """Particle composed of connected line points. Useful for wire/mesh/trail shapes."""

    def __init__(
        self,
        points: list[tuple],
        color: Tuple[int, int, int] = (255, 255, 255),
        life: int = 60,
        width: int = 2,
    ):
        # points: list of (x, y) in camera coordinates
        self.points = [(float(x), float(y)) for x, y in points]
        self.color = color
        self.life = life
        self.age = 0
        self.max_life = life
        self.width = width

    def update(self):
        self.age += 1

    def is_dead(self) -> bool:
        return self.age >= self.life

    def draw_pygame(self, surface, scale_x: float = 1.0, scale_y: float = 1.0):
        alpha = max(0.0, 1.0 - (self.age / max(1, self.max_life)))
        r, g, b = self.color
        color = (int(r), int(g), int(b), int(255 * alpha))
        scaled = [(int(x * scale_x), int(y * scale_y)) for x, y in self.points]
        if len(scaled) >= 2:
            pygame.draw.lines(
                surface,
                color,
                False,
                scaled,
                max(1, int(self.width * max(scale_x, scale_y))),
            )


def create_wire_triangle(x: int, y: int, size: int = 80):
    # triangle points centered at (x, y)
    p1 = (x, y - size // 2)
    p2 = (x - size // 2, y + size // 3)
    p3 = (x + size // 2, y + size // 3)
    points = [p1, p2, p3, p1]
    return LineParticle(points, color=(255, 100, 200), life=80, width=2)


def create_orbit_line(x: int, y: int, radius: int = 60, segments: int = 28):
    points = []
    for i in range(segments + 1):
        a = (
            i / segments * math.tau
            if hasattr(math, "tau")
            else i / segments * 2 * math.pi
        )
        px = x + math.cos(a) * radius
        py = y + math.sin(a) * radius
        points.append((px, py))
    return LineParticle(points, color=(255, 220, 120), life=100, width=2)


def create_fan(x: int, y: int, length: int = 80, count: int = 5):
    points = []
    # fan spreads from -45deg to +45deg
    for i in range(count):
        angle = -math.pi / 4 + i * (math.pi / 2) / max(1, count - 1)
        px = x + math.cos(angle) * length
        py = y + math.sin(angle) * length
        points.append((x, y))
        points.append((px, py))
    return LineParticle(points, color=(120, 200, 255), life=60, width=2)


# -----------------------------
# Pseudo-3D particle utilities
# -----------------------------


def project_point(
    x: float,
    y: float,
    z: float,
    *,
    scale: float = 900.0,
    depth: float = 350.0,
) -> tuple[float, float, float]:
    """Project a 3D point to 2D screen space using simple perspective."""
    denom = z + depth
    if denom < 1.0:
        denom = 1.0
    p = scale / denom
    return x * p, y * p, p


def _draw_additive_tiny_point(
    surface,
    cx: int,
    cy: int,
    color: Tuple[int, int, int],
    alpha: int,
    *,
    pixel_size: int = 1,
) -> None:
    """Draw a small sci-fi dot with a subtle halo using rect pixels."""
    pygame.draw.rect(
        surface,
        (*color, alpha),
        pygame.Rect(cx, cy, pixel_size, pixel_size),
    )

    # small halo pixels for softness (still dot-based, not bubble-like)
    halo_alpha = max(0, alpha // 4)
    if halo_alpha > 0:
        halo_color = (*color, halo_alpha)
        pygame.draw.rect(surface, halo_color, pygame.Rect(cx + 1, cy, 1, 1))
        pygame.draw.rect(surface, halo_color, pygame.Rect(cx - 1, cy, 1, 1))
        pygame.draw.rect(surface, halo_color, pygame.Rect(cx, cy + 1, 1, 1))
        pygame.draw.rect(surface, halo_color, pygame.Rect(cx, cy - 1, 1, 1))
        pygame.draw.rect(surface, halo_color, pygame.Rect(cx + 1, cy + 1, 1, 1))
        pygame.draw.rect(surface, halo_color, pygame.Rect(cx - 1, cy - 1, 1, 1))


def rotate_point(
    x: float,
    y: float,
    z: float,
    *,
    rot_x: float = 0.0,
    rot_y: float = 0.0,
    rot_z: float = 0.0,
) -> tuple[float, float, float]:
    """Rotate a 3D point around X/Y/Z axes."""
    # Z rotation
    cosz = math.cos(rot_z)
    sinz = math.sin(rot_z)
    x, y = x * cosz - y * sinz, x * sinz + y * cosz

    # X rotation
    cosx = math.cos(rot_x)
    sinx = math.sin(rot_x)
    y, z = y * cosx - z * sinx, y * sinx + z * cosx

    # Y rotation
    cosy = math.cos(rot_y)
    siny = math.sin(rot_y)
    x, z = x * cosy + z * siny, -x * siny + z * cosy

    return x, y, z


class Particle3D:
    """A pseudo-3D particle with steering toward a 3D target and orbit/noise motion."""

    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        *,
        target_x: float | None = None,
        target_y: float | None = None,
        target_z: float | None = None,
        color: Tuple[int, int, int] = (255, 220, 120),
        size: int | None = None,
        life: int = 180,
        speed: float = 0.04,
        orbit_strength: float = 0.08,
        noise: float = 0.02,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

        self.vx = random.uniform(-1.0, 1.0) * speed
        self.vy = random.uniform(-1.0, 1.0) * speed
        self.vz = random.uniform(-1.0, 1.0) * speed

        self.target_x = float(target_x if target_x is not None else x)
        self.target_y = float(target_y if target_y is not None else y)
        self.target_z = float(target_z if target_z is not None else z)

        self.color = color
        self.size = size if size is not None else random.randint(4, 7)
        self.life = life
        self.age = 0

        self.speed = speed
        self.orbit_strength = orbit_strength
        self.noise = noise
        self.phase = random.uniform(0.0, math.tau)

    def set_target(self, x: float, y: float, z: float) -> None:
        self.target_x = float(x)
        self.target_y = float(y)
        self.target_z = float(z)

    def update(self):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dz = self.target_z - self.z

        dist = math.sqrt(dx * dx + dy * dy + dz * dz) + 1e-6
        steer = self.speed * (1.5 if dist > 60 else 0.7)

        self.vx += (dx / dist) * steer
        self.vy += (dy / dist) * steer
        self.vz += (dz / dist) * steer

        self.phase += 0.08
        self.vx += math.cos(self.phase) * self.orbit_strength + random.uniform(
            -self.noise, self.noise
        )
        self.vy += math.sin(self.phase * 1.2) * self.orbit_strength + random.uniform(
            -self.noise, self.noise
        )
        self.vz += math.sin(self.phase * 0.7) * self.orbit_strength + random.uniform(
            -self.noise, self.noise
        )

        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        self.vx *= 0.96
        self.vy *= 0.96
        self.vz *= 0.96

        self.age += 1

    def is_dead(self) -> bool:
        return self.age >= self.life

    def draw_pygame(
        self,
        surface,
        screen_w: int | None = None,
        screen_h: int | None = None,
        *,
        scale: float = 900.0,
        depth: float = 350.0,
        rot_x: float = 0.0,
        rot_y: float = 0.0,
        rot_z: float = 0.0,
    ):
        if screen_w is None or screen_h is None:
            screen_w, screen_h = surface.get_size()

        alpha = max(0.0, 1.0 - (self.age / max(1, self.life)))
        rx, ry, rz = rotate_point(
            self.x, self.y, self.z, rot_x=rot_x, rot_y=rot_y, rot_z=rot_z
        )
        sx, sy, p = project_point(rx, ry, rz, scale=scale, depth=depth)
        cx = int(screen_w / 2 + sx)
        cy = int(screen_h / 2 + sy)

        r, g, b = self.color
        # keep the point-cloud readable with small sci-fi dots.
        pixel_size = max(2, min(4, self.size))
        point_alpha = int(255 * alpha)
        _draw_additive_tiny_point(
            surface,
            cx,
            cy,
            (int(r), int(g), int(b)),
            point_alpha,
            pixel_size=pixel_size,
        )


def make_point_cloud_letter(
    letter: str, *, spacing: int = 18
) -> list[tuple[float, float, float]]:
    """Generate a simple 3D point cloud for a few letters."""
    letter = (letter or "").upper()
    pts: list[tuple[float, float, float]] = []

    def push(x: float, y: float, z: float = 0.0):
        pts.append((x, y, z + random.uniform(-90, 90)))

    if letter == "L":
        for y in range(-90, 91, spacing):
            push(-40, y, 0)
        for x in range(-40, 61, spacing):
            push(x, 90, 0)
    elif letter == "A":
        for y in range(-80, 21, spacing):
            t = (y + 80) / 100.0
            push(-50 + t * 50, y, 0)
            push(50 - t * 50, y, 0)
        for x in range(-20, 21, spacing):
            push(x, 0, 0)
    elif letter == "T":
        for x in range(-70, 71, spacing):
            push(x, -80, 0)
        for y in range(-80, 91, spacing):
            push(0, y, 0)
    elif letter == "V":
        for y in range(-90, 61, spacing):
            t = (y + 90) / 150.0
            push(-60 + t * 60, y, 0)
            push(60 - t * 60, y, 0)
    elif letter == "Y":
        for y in range(-80, 1, spacing):
            push(0, y, 0)
        for x in range(-60, 61, spacing):
            push(x * 0.5, 20 + abs(x) * 0.2, 0)
    else:
        for i in range(36):
            a = i / 36.0 * math.tau
            push(math.cos(a) * 60, math.sin(a) * 60, 0)

    return pts


def make_text_pixel_targets(
    text: str,
    *,
    font_size: int = 220,
    sample_step: int = 2,
    scale: float = 0.58,
    depth_span: float = 110.0,
) -> list[tuple[float, float, float]]:
    """Render text to a pixel map and convert bright pixels into 3D target points.

    This is the preferred generator for cinematic holographic typography.
    """
    if pygame is None:
        return make_point_cloud_letter(text, spacing=max(8, sample_step * 2))

    if not pygame.font.get_init():
        pygame.font.init()

    text = (text or "").strip() or "L"

    font_candidates = [
        "Arial",
        "DejaVu Sans",
        "Liberation Sans",
        None,
    ]
    font = None
    for name in font_candidates:
        try:
            if name is None:
                font = pygame.font.Font(None, font_size)
            else:
                font = pygame.font.SysFont(name, font_size, bold=True)
            test = font.render(text, True, (255, 255, 255))
            if test.get_width() > 0 and test.get_height() > 0:
                break
        except Exception:
            font = None
            continue

    if font is None:
        return make_point_cloud_letter(text, spacing=max(8, sample_step * 2))

    surf = font.render(text, True, (255, 255, 255))
    w, h = surf.get_size()
    targets: list[tuple[float, float, float]] = []

    # Sample the alpha / brightness map; pixels above threshold become targets.
    for y in range(0, h, sample_step):
        for x in range(0, w, sample_step):
            px = surf.get_at((x, y))
            intensity = max(px.r, px.g, px.b, px.a)
            if intensity < 18:
                continue

            nx = (x - w / 2) * scale
            ny = (y - h / 2) * scale

            # Depth spread: keep the center slightly denser and let edges float a bit.
            edge_dist = abs(x - w / 2) / max(1.0, w / 2)
            z = random.uniform(-depth_span, depth_span) * (0.35 + edge_dist * 0.65)

            # duplicate some pixels into a tiny depth stack to get volumetric density
            targets.append((nx, ny, z))
            if intensity > 200 and random.random() < 0.55:
                targets.append(
                    (
                        nx + random.uniform(-2, 2),
                        ny + random.uniform(-2, 2),
                        z + random.uniform(-25, 25),
                    )
                )

    return targets


def make_strong_letter_L_targets(
    *,
    scale: float = 1.0,
    depth_span: float = 58.0,
) -> list[tuple[float, float, float]]:
    """Generate a bold 3D L-shaped point cloud with a clear stem and base."""
    targets: list[tuple[float, float, float]] = []

    # A cleaner L: thick stem + shorter base, with depth stacked across three planes.
    # The corner is reinforced, but not overfilled into a square.
    stem_left = -86.0
    stem_right = -48.0
    stem_top = -132.0
    stem_bottom = 108.0

    base_left = -86.0
    base_right = 176.0
    base_top = 66.0
    base_bottom = 112.0

    def add_layered_bar(
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        *,
        z_center: float,
        z_thickness: float,
        jitter_xy: float,
        sample_step: int,
        density: float,
    ) -> None:
        for z in range(-int(z_thickness), int(z_thickness) + 1, 14):
            z_weight = 1.0 - abs(z) / max(1.0, z_thickness)
            for y in range(int(y0), int(y1) + 1, sample_step):
                for x in range(int(x0), int(x1) + 1, sample_step):
                    # carve out the upper-right of the vertical stem so it reads like an L,
                    # not a rectangle.
                    if (
                        x > stem_right - 6
                        and y < 58
                        and (x - stem_right) + (58 - y) > 42
                    ):
                        continue
                    if random.random() > density:
                        continue

                    # give the prism a slight perspective skew across depth.
                    depth_shift = (z / max(1.0, z_thickness)) * 7.0
                    x_shift = depth_shift * 0.35
                    y_shift = depth_shift * 0.18
                    targets.append(
                        (
                            (x + random.uniform(-jitter_xy, jitter_xy) + x_shift)
                            * scale,
                            (y + random.uniform(-jitter_xy, jitter_xy) + y_shift)
                            * scale,
                            z_center + z + random.uniform(-3.5, 3.5) * z_weight,
                        )
                    )
                    if random.random() < 0.28 + z_weight * 0.2:
                        targets.append(
                            (
                                (x + random.uniform(-jitter_xy, jitter_xy) + x_shift)
                                * scale,
                                (y + random.uniform(-jitter_xy, jitter_xy) + y_shift)
                                * scale,
                                z_center + z + random.uniform(-6.0, 6.0) * z_weight,
                            )
                        )

    # Stem: thick 3D column.
    add_layered_bar(
        stem_left,
        stem_top,
        stem_right,
        stem_bottom,
        z_center=-18.0,
        z_thickness=depth_span * 0.7,
        jitter_xy=0.30,
        sample_step=2,
        density=0.93,
    )

    # Base: thick 3D floor bar.
    add_layered_bar(
        base_left,
        base_top,
        base_right,
        base_bottom,
        z_center=12.0,
        z_thickness=depth_span * 0.62,
        jitter_xy=0.34,
        sample_step=2,
        density=0.92,
    )

    # Corner reinforcement: enough mass to connect the bars, but not a square blob.
    add_layered_bar(
        -84.0,
        56.0,
        -52.0,
        104.0,
        z_center=0.0,
        z_thickness=depth_span * 0.42,
        jitter_xy=0.28,
        sample_step=2,
        density=0.95,
    )

    return targets


def create_3d_letter_particles(
    letter: str,
    *,
    count_multiplier: int = 3,
    depth_base: float = 300.0,
    color: Tuple[int, int, int] = (120, 220, 255),
) -> list[Particle3D]:
    """Create Particle3D objects around a point-cloud letter."""
    pts = make_point_cloud_letter(letter)
    particles: list[Particle3D] = []
    if not pts:
        return particles

    for px, py, pz in pts:
        for _ in range(max(1, count_multiplier)):
            particles.append(
                Particle3D(
                    px + random.uniform(-40, 40),
                    py + random.uniform(-40, 40),
                    depth_base + pz + random.uniform(-40, 40),
                    target_x=px,
                    target_y=py,
                    target_z=depth_base + pz,
                    color=color,
                    size=random.randint(5, 8),
                    life=random.randint(120, 220),
                    speed=random.uniform(0.02, 0.07),
                    orbit_strength=random.uniform(0.02, 0.12),
                    noise=random.uniform(0.0, 0.03),
                )
            )

    return particles


def make_abstract_3d_targets(
    count: int = 220, radius: float = 170.0
) -> list[tuple[float, float, float]]:
    """Generate a reusable abstract 3D target cloud (ring/sphere-ish)."""
    targets: list[tuple[float, float, float]] = []
    for i in range(count):
        a = (i / max(1, count)) * math.tau
        b = random.uniform(-math.pi / 2.2, math.pi / 2.2)
        r = radius * random.uniform(0.55, 1.05)

        x = math.cos(a) * math.cos(b) * r
        y = math.sin(a) * math.cos(b) * r
        z = math.sin(b) * r * 0.7 + random.uniform(-35, 35)
        targets.append((x, y, z))
    return targets


class MorphCloud3D:
    """Persistent pseudo-3D swarm that can morph between abstract targets and letter targets."""

    def __init__(
        self,
        count: int = 240,
        *,
        base_color: Tuple[int, int, int] = (240, 220, 180),
        depth_base: float = 320.0,
        scale: float = 900.0,
        depth: float = 350.0,
        center_x: float = 0.0,
        center_y: float = 0.0,
        center_z: float = 0.0,
    ):
        self.base_color = base_color
        self.depth_base = depth_base
        self.scale = scale
        self.depth = depth
        self.center_x = center_x
        self.center_y = center_y
        self.center_z = center_z
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.rot_z = 0.0
        self.mode = "abstract"
        self.focus_letter = ""

        self.particles: list[Particle3D] = []
        self.target_points: list[tuple[float, float, float]] = []

        self._build_swarm(count)
        self.set_abstract_targets()

    def _build_swarm(self, count: int) -> None:
        self.particles = []
        for _ in range(count):
            self.particles.append(
                Particle3D(
                    random.uniform(-180, 180),
                    random.uniform(-180, 180),
                    random.uniform(120, 520),
                    target_x=random.uniform(-180, 180),
                    target_y=random.uniform(-180, 180),
                    target_z=random.uniform(120, 520),
                    color=self.base_color,
                    size=random.randint(3, 5),
                    life=10_000,
                    speed=random.uniform(0.01, 0.035),
                    orbit_strength=random.uniform(0.01, 0.08),
                    noise=random.uniform(0.0, 0.015),
                )
            )

    def set_abstract_targets(self) -> None:
        self.mode = "abstract"
        self.focus_letter = ""
        self.target_points = make_abstract_3d_targets(len(self.particles), radius=170.0)
        self._apply_targets(self.target_points)

        # restore a more organic abstract motion
        for p in self.particles:
            p.speed = random.uniform(0.01, 0.035)
            p.orbit_strength = random.uniform(0.01, 0.08)
            p.noise = random.uniform(0.0, 0.015)

    def set_letter_targets(self, letter: str) -> None:
        self.mode = letter.upper() if letter else "abstract"
        self.focus_letter = self.mode

        # Make L more readable by using a stronger explicit L geometry.
        if self.mode == "L":
            pts = make_strong_letter_L_targets(scale=1.0, depth_span=95.0)
        else:
            # Text-pixel map creates the dense holographic typography look.
            pts = make_text_pixel_targets(
                letter, font_size=240, sample_step=2, scale=0.56, depth_span=140.0
            )

        self.target_points = pts or make_abstract_3d_targets(
            len(self.particles), radius=170.0
        )
        self._apply_targets(self.target_points)

        # calm the motion so the L settles and reads clearly
        for p in self.particles:
            if self.mode == "L":
                p.size = max(p.size, 6)
                p.speed = 0.24
                p.orbit_strength = 0.0
                p.noise = 0.0
                # Keep the current scattered positions; the stronger speed makes them converge quickly.
                p.vx *= 0.06
                p.vy *= 0.06
                p.vz *= 0.06
            else:
                p.size = max(p.size, 4)
                p.speed = 0.032
                p.orbit_strength = 0.0025
                p.noise = 0.0

    def _apply_targets(self, target_points: list[tuple[float, float, float]]) -> None:
        if not target_points:
            return
        for i, p in enumerate(self.particles):
            tx, ty, tz = target_points[i % len(target_points)]
            p.set_target(tx + self.center_x, ty + self.center_y, tz + self.center_z)

    def update(self) -> None:
        # gentle scene rotation so the cloud never feels flat
        if self.focus_letter == "L":
            # keep L readable, but allow a subtle 3D reveal.
            self.rot_x = self.rot_x * 0.992 + 0.00025
            self.rot_y = self.rot_y * 0.992 + 0.00035
            self.rot_z = self.rot_z * 0.992 + 0.00055
        else:
            self.rot_x += 0.004
            self.rot_y += 0.007
            self.rot_z += 0.0015

        for p in self.particles:
            # a tiny pull toward the anchor center keeps the whole cloud stable
            if self.focus_letter == "L":
                # Stronger target pull so the shape locks in much faster.
                p.vx += (p.target_x - p.x) * 0.00036
                p.vy += (p.target_y - p.y) * 0.00036
                p.vz += (p.target_z - p.z) * 0.00026

                # Still keep a slight anchor so the whole letter doesn't drift.
                p.vx += (self.center_x - p.x) * 0.00002
                p.vy += (self.center_y - p.y) * 0.00002
                p.vz += (self.center_z - p.z) * 0.00001
            else:
                p.vx += (self.center_x - p.x) * 0.00005
                p.vy += (self.center_y - p.y) * 0.00005
                p.vz += (self.center_z - p.z) * 0.00003
            p.update()

    def draw(self, surface) -> None:
        w, h = surface.get_size()
        glow_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # depth sort so nearer particles paint on top
        draw_list = []
        for p in self.particles:
            rx, ry, rz = rotate_point(
                p.x, p.y, p.z, rot_x=self.rot_x, rot_y=self.rot_y, rot_z=self.rot_z
            )
            draw_list.append((rz, p, rx, ry))

        for rz, p, rx, ry in sorted(draw_list, key=lambda item: item[0]):
            # draw through a small helper by projecting the rotated coords
            sx, sy, persp = project_point(
                rx, ry, rz, scale=self.scale, depth=self.depth
            )
            cx = int(w / 2 + sx)
            cy = int(h / 2 + sy)

            alpha = max(0.0, 1.0 - (p.age / max(1, p.life)))
            r, g, b = p.color
            # small sci-fi dots; density comes from count, not oversized shapes
            pixel_size = 2 if persp > 0.85 else 3
            point_alpha = int(255 * alpha)

            # core point
            _draw_additive_tiny_point(
                glow_layer,
                cx,
                cy,
                (r, g, b),
                point_alpha,
                pixel_size=pixel_size,
            )

            # extra tiny noise to mimic a dense energy field
            if random.random() < 0.22:
                jitter_alpha = max(0, point_alpha // 4)
                _draw_additive_tiny_point(
                    glow_layer,
                    cx + 1,
                    cy,
                    (r, g, b),
                    jitter_alpha,
                    pixel_size=2,
                )
                _draw_additive_tiny_point(
                    glow_layer,
                    cx,
                    cy + 1,
                    (r, g, b),
                    jitter_alpha,
                    pixel_size=2,
                )

        # add bloom to main surface to emulate bright glowing cloud
        surface.blit(glow_layer, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_wire_letter(self, surface, letter: str) -> None:
        """Draw a glowing wire-outline of the focus letter in pseudo-3D space."""
        w, h = surface.get_size()

        def wire_points_L() -> tuple[
            list[tuple[float, float, float]], list[tuple[float, float, float]]
        ]:
            vertical: list[tuple[float, float, float]] = []
            bottom: list[tuple[float, float, float]] = []
            # vertical stroke
            for y in range(-92, 93, 8):
                vertical.append((-50.0, float(y), 40.0 * math.sin(y / 40.0)))
            # bottom stroke
            for x in range(-50, 86, 8):
                bottom.append((float(x), 90.0, 40.0 * math.cos(x / 36.0)))
            return vertical, bottom

        if letter != "L":
            return

        vertical_pts, bottom_pts = wire_points_L()
        projected_vertical: list[tuple[int, int]] = []
        projected_bottom: list[tuple[int, int]] = []

        for x, y, z in vertical_pts:
            rx, ry, rz = rotate_point(
                x, y, z, rot_x=self.rot_x, rot_y=self.rot_y, rot_z=self.rot_z
            )
            sx, sy, _ = project_point(
                rx, ry, rz, scale=self.scale * 1.15, depth=self.depth - 30
            )
            projected_vertical.append((int(w / 2 + sx), int(h / 2 + sy)))

        for x, y, z in bottom_pts:
            rx, ry, rz = rotate_point(
                x, y, z, rot_x=self.rot_x, rot_y=self.rot_y, rot_z=self.rot_z
            )
            sx, sy, _ = project_point(
                rx, ry, rz, scale=self.scale * 1.15, depth=self.depth - 30
            )
            projected_bottom.append((int(w / 2 + sx), int(h / 2 + sy)))

        # draw with glow layers; split into vertical and horizontal parts visually
        wire_color = (255, 240, 120)
        for width, alpha_mul in ((18, 18), (10, 40), (4, 255)):
            glow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            if len(projected_vertical) >= 2:
                pygame.draw.lines(
                    glow,
                    (*wire_color, alpha_mul),
                    False,
                    projected_vertical,
                    width,
                )
            if len(projected_bottom) >= 2:
                pygame.draw.lines(
                    glow,
                    (*wire_color, alpha_mul),
                    False,
                    projected_bottom,
                    width,
                )
            surface.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
