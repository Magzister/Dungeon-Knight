"""Browser-independent movement, collision, and DDA raycasting."""

from dataclasses import dataclass
from math import cos, floor, hypot, sin


class Room:
    def __init__(self, data):
        self.tiles = data["map"]
        self.height = len(self.tiles)
        self.width = len(self.tiles[0])
        if any(len(row) != self.width for row in self.tiles):
            raise ValueError("Room rows must have equal widths")

    def tile(self, x, y):
        x, y = floor(x), floor(y)
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 1
        return int(self.tiles[y][x])

    def clear(self, x, y, radius=0.20):
        return all(not self.tile(x + dx, y + dy)
                   for dx in (-radius, radius) for dy in (-radius, radius))

    def cast(self, x, y, dx, dy):
        """Return perpendicular distance, wall texture offset, material, side."""
        mx, my = floor(x), floor(y)
        delta_x = abs(1 / dx) if dx else float("inf")
        delta_y = abs(1 / dy) if dy else float("inf")
        step_x, step_y = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
        side_x = ((mx + 1 - x) if dx >= 0 else (x - mx)) * delta_x
        side_y = ((my + 1 - y) if dy >= 0 else (y - my)) * delta_y
        for _ in range(self.width + self.height + 2):
            if side_x < side_y:
                side_x += delta_x
                mx += step_x
                distance, side = side_x - delta_x, 0
            else:
                side_y += delta_y
                my += step_y
                distance, side = side_y - delta_y, 1
            material = self.tile(mx, my)
            if material:
                hit = y + distance * dy if side == 0 else x + distance * dx
                return max(0.001, distance), hit % 1, material, side
        raise RuntimeError("Ray failed to hit the room boundary")


@dataclass
class Player:
    x: float
    y: float
    angle: float

    def move(self, room, forward, strafe, dt, sprint=False):
        length = hypot(forward, strafe)
        if not length:
            return False
        speed = (3.4 if sprint else 2.1) * min(dt, 0.05) / max(1, length)
        dx = (cos(self.angle) * forward - sin(self.angle) * strafe) * speed
        dy = (sin(self.angle) * forward + cos(self.angle) * strafe) * speed
        old = self.x, self.y
        if room.clear(self.x + dx, self.y):
            self.x += dx
        if room.clear(self.x, self.y + dy):
            self.y += dy
        return old != (self.x, self.y)
