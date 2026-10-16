import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web"))
from core import Player, Room


class DungeonTests(unittest.TestCase):
    def setUp(self):
        self.room = Room({"map": ["11111", "10001", "10001", "10001", "11111"]})

    def test_cardinal_rays(self):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            distance, offset, material, side = self.room.cast(2.5, 2.5, dx, dy)
            self.assertAlmostEqual(distance, 1.5)
            self.assertEqual(material, 1)
            self.assertTrue(0 <= offset < 1)

    def test_diagonal_ray(self):
        self.assertAlmostEqual(self.room.cast(2.5, 2.5, 1, 1)[0], 1.5)

    def test_collision_and_sliding(self):
        player = Player(3.79, 2.5, 0)
        player.move(self.room, 1, 1, .05)
        self.assertEqual(player.x, 3.79)
        self.assertGreater(player.y, 2.5)
        self.assertTrue(self.room.clear(player.x, player.y))

    def test_movement_is_normalized_and_dt_is_capped(self):
        straight, diagonal = Player(2, 2, 0), Player(2, 2, 0)
        straight.move(self.room, 1, 0, .05)
        diagonal.move(self.room, 1, 1, 10)
        self.assertAlmostEqual(math.hypot(diagonal.x - 2, diagonal.y - 2), straight.x - 2)

    def test_room_spawn_and_all_directions(self):
        data = json.loads((ROOT / "web/room.json").read_text())
        room, player = Room(data), Player(**data["spawn"])
        self.assertTrue(room.clear(player.x, player.y))
        for angle in range(360):
            distance, offset, material, side = room.cast(player.x, player.y, math.cos(math.radians(angle)), math.sin(math.radians(angle)))
            self.assertGreater(distance, 0)
            self.assertIn(material, (1, 2, 3))

    def test_outside_room_is_solid(self):
        self.assertEqual(self.room.tile(-.1, 2), 1)
        self.assertFalse(self.room.clear(.1, 2))


if __name__ == "__main__":
    unittest.main()
