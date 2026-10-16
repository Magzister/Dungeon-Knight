"""Python browser client: canvas raycaster, controls, and a knight's sword."""

import math
import random

import js
from pyodide.ffi import create_proxy
from zapros import AsyncClient

from core import Player, Room

W, H = 640, 400
FOV = 0.70  # camera-plane half width; about 70 degrees horizontally
FOCAL = W / (2 * FOV)
document = js.document
canvas = document.getElementById("game")
ctx = canvas.getContext("2d", {"alpha": False})
proxies = []  # Event callbacks must remain alive while JavaScript holds them.


def listen(target, name, callback):
    proxy = create_proxy(callback)
    proxies.append(proxy)
    target.addEventListener(name, proxy)


def polygon(context, points, fill, stroke=None):
    context.beginPath()
    context.moveTo(*points[0])
    for point in points[1:]:
        context.lineTo(*point)
    context.closePath()
    context.fillStyle = fill
    context.fill()
    if stroke:
        context.strokeStyle = stroke
        context.lineWidth = 1
        context.stroke()


def surface(width, height):
    image = document.createElement("canvas")
    image.width, image.height = width, height
    return image, image.getContext("2d")


def make_wall(material):
    image, c = surface(128, 128)
    rng = random.Random(81 + material)
    c.fillStyle = "#252923"
    c.fillRect(0, 0, 128, 128)
    if material == 2:
        for x in range(0, 128, 16):
            shade = rng.randrange(35, 50)
            c.fillStyle = f"rgb({shade + 13},{shade + 4},{shade - 10})"
            c.fillRect(x + 1, 0, 14, 128)
            c.fillStyle = "#1b201b"
            c.fillRect(x + 12, 0, 1, 128)
        for y in (24, 95):
            c.fillStyle = "#272e2c"
            c.fillRect(0, y, 128, 8)
            c.fillStyle = "#6d6d4a"
            c.fillRect(0, y, 128, 1)
            for x in range(8, 128, 16):
                c.fillStyle = "#777458"
                c.fillRect(x, y + 3, 2, 2)
        c.strokeStyle = "#818b68"
        c.lineWidth = 2
        c.beginPath()
        c.moveTo(64, 41)
        for x, y in ((75, 58), (64, 78), (53, 58), (64, 41), (64, 78)):
            c.lineTo(x, y)
        c.stroke()
        return image
    for row in range(4):
        for col in range(-1, 3):
            x, y = col * 64 + (32 if row % 2 else 0), row * 32
            shade = rng.randrange(64, 88)
            c.fillStyle = f"rgb({shade},{shade + 3},{shade - 5})"
            c.fillRect(x + 2, y + 2, 61, 29)
            c.fillStyle = "#9b9b7d33"
            c.fillRect(x + 3, y + 2, 59, 2)
            c.fillStyle = "#0d17175c"
            c.fillRect(x + 2, y + 28, 61, 3)
            for _ in range(75):
                px, py = x + rng.randrange(3, 61), y + rng.randrange(4, 28)
                c.fillStyle = rng.choice(("#c6bfa812", "#08171322", "#d1c9ab16"))
                c.fillRect(px, py, rng.randrange(1, 6), 1)
            if rng.random() > .5:
                c.strokeStyle = "#27312b70"
                c.beginPath()
                c.moveTo(x + 30, y + 3)
                c.lineTo(x + 25, y + 12)
                c.lineTo(x + 29, y + 17)
                c.stroke()
    if material == 3:
        for _ in range(190):
            c.fillStyle = rng.choice(("#384c2e77", "#263c2c88", "#6d71403c"))
            c.fillRect(rng.randrange(128), rng.randrange(128), rng.randrange(2, 12), rng.randrange(2, 9))
    return image


def make_sprite(kind):
    image, c = surface(96, 128)
    if kind == "torch":
        c.fillStyle = "#161c19"
        c.fillRect(41, 67, 15, 48)
        polygon(c, [(39, 94), (56, 94), (62, 70), (35, 70)], "#4a4938", "#8d8061")
        c.fillStyle = "#65482c"
        c.fillRect(44, 39, 8, 39)
        glow = c.createRadialGradient(48, 36, 1, 48, 36, 35)
        glow.addColorStop(0, "#ffc35faa")
        glow.addColorStop(1, "#e56d0000")
        c.fillStyle = glow
        c.fillRect(9, 0, 78, 76)
        polygon(c, [(48, 5), (44, 22), (34, 34), (38, 48), (47, 56), (59, 45), (61, 33), (53, 24), (53, 16)], "#dd702c")
        polygon(c, [(47, 18), (43, 34), (42, 44), (49, 51), (55, 42), (52, 33)], "#ffce73")
        polygon(c, [(48, 30), (46, 43), (50, 48), (52, 41)], "#fff1b8")
    elif kind == "barrel":
        polygon(c, [(23, 43), (71, 43), (80, 57), (79, 113), (68, 124), (26, 124), (17, 111), (16, 59)], "#503d29", "#211e18")
        for x in range(24, 75, 9):
            c.fillStyle = "#302b1f"
            c.fillRect(x, 55, 2, 63)
            c.fillStyle = "#9d744330"
            c.fillRect(x + 3, 57, 3, 60)
        for y in (62, 104):
            c.fillStyle = "#333c36"
            c.fillRect(18, y, 61, 9)
            c.fillStyle = "#7c7962"
            c.fillRect(20, y, 57, 2)
            for x in (25, 47, 69):
                c.fillStyle = "#9b9170"
                c.fillRect(x, y + 3, 2, 2)
        polygon(c, [(23, 43), (70, 43), (77, 53), (19, 53)], "#786044", "#9c8052")
    else:
        polygon(c, [(8, 80), (76, 80), (91, 91), (91, 122), (8, 122)], "#494e45", "#727461")
        polygon(c, [(4, 77), (77, 77), (95, 89), (19, 89)], "#8a8b72")
        polygon(c, [(19, 89), (95, 89), (95, 97), (19, 97)], "#656b5a")
        c.fillStyle = "#333b34"
        c.fillRect(33, 101, 42, 17)
        c.fillStyle = "#a69969"
        c.font = "13px serif"
        c.fillText("ᛟ ᛞ ᛟ", 36, 114)
        polygon(c, [(30, 75), (53, 70), (68, 74), (47, 81)], "#925240", "#cfab72")
        polygon(c, [(47, 81), (68, 74), (68, 77), (47, 84)], "#d2bd8b")
    return image


class Game:
    def __init__(self, data):
        self.data = data
        self.room = Room(data)
        self.player = Player(**data["spawn"])
        self.keys = set()
        self.active = False
        self.pitch = 0
        self.swing = 0
        self.bob = 0
        self.last_time = None
        self.fps_time = 0
        self.frames = 0
        self.elapsed = 0
        self.textures = {i: make_wall(i) for i in (1, 2, 3)}
        self.sprites = {kind: make_sprite(kind) for kind in ("torch", "barrel", "altar")}
        self.objects = [(x, y, "torch") for x, y in data["torches"]]
        self.objects += [(x, y, "barrel") for x, y in data["barrels"]]
        self.objects.append((*data["altar"], "altar"))
        self.audio = None
        self.audio_nodes = []
        self.note = document.getElementById("room-note")
        self.overlay = document.getElementById("overlay")
        self.enter = document.getElementById("enter")
        self.frame_proxy = create_proxy(self.frame)
        proxies.append(self.frame_proxy)
        listen(self.enter, "click", self.capture)
        listen(canvas, "click", self.click)
        listen(document, "pointerlockchange", self.lock_changed)
        listen(document, "pointerlockerror", self.lock_failed)
        listen(document, "keydown", self.keydown)
        listen(document, "keyup", lambda event: self.keys.discard(event.code))
        listen(document, "mousemove", self.mouse)
        listen(js.window, "blur", self.pause)
        listen(document, "visibilitychange", self.visibility)
        listen(document.getElementById("fullscreen"), "click", self.fullscreen)
        listen(document.getElementById("sound"), "click", self.toggle_sound)
        self.enter.disabled = False
        self.enter.textContent = "Enter the keep  →"
        document.getElementById("status").textContent = "Click to begin · Headphones recommended"
        self.render()
        js.requestAnimationFrame(self.frame_proxy)

    def capture(self, event=None):
        # Called directly from the click so pointer lock retains user activation.
        self.active = True
        self.overlay.classList.add("hidden")
        canvas.focus()
        try:
            promise = canvas.requestPointerLock()
            if promise:
                promise.catch(js.Function.new("console.info('Pointer lock unavailable; use arrow keys to look.')"))
        except Exception:
            self.lock_failed()

    def lock_failed(self, event=None):
        self.note.textContent = "Use arrow keys to look · Esc to pause"

    def click(self, event):
        if not self.active:
            self.capture()
        else:
            self.attack()

    def attack(self):
        if self.swing <= 0:
            self.swing = .48

    def pause(self, event=None):
        self.active = False
        self.keys.clear()
        self.overlay.classList.remove("hidden")
        self.enter.textContent = "Return to the keep  →"
        document.getElementById("status").textContent = "Your journey is paused"

    def visibility(self, event):
        if document.hidden:
            self.pause()

    def lock_changed(self, event):
        if document.pointerLockElement != canvas:
            self.pause()

    def keydown(self, event):
        if not self.active:
            return
        if event.code in ("KeyW", "KeyA", "KeyS", "KeyD", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space", "ShiftLeft", "ShiftRight", "Escape"):
            event.preventDefault()
            self.keys.add(event.code)
        if event.code == "Escape":
            self.pause()
            if document.pointerLockElement == canvas:
                document.exitPointerLock()
        elif event.code == "Space":
            self.attack()

    def mouse(self, event):
        if self.active and document.pointerLockElement == canvas:
            self.player.angle += event.movementX * .0025
            self.pitch = max(-65, min(65, self.pitch - event.movementY * .22))

    async def fullscreen(self, event):
        try:
            if document.fullscreenElement:
                await document.exitFullscreen()
            else:
                await document.getElementById("viewport").requestFullscreen()
        except Exception:
            self.note.textContent = "Fullscreen is unavailable in this browser"

    async def toggle_sound(self, event):
        button = document.getElementById("sound")
        if self.audio is None:
            self.audio = js.AudioContext.new()
            # A quiet two-note drone; generated locally, no audio assets needed.
            for frequency in (55, 82.41):
                oscillator = self.audio.createOscillator()
                gain = self.audio.createGain()
                oscillator.type = "sine"
                oscillator.frequency.value = frequency
                gain.gain.value = .025
                oscillator.connect(gain)
                gain.connect(self.audio.destination)
                oscillator.start()
                self.audio_nodes.extend((oscillator, gain))
        if button.getAttribute("aria-pressed") == "true":
            await self.audio.suspend()
            button.textContent = "SOUND OFF"
            button.setAttribute("aria-pressed", "false")
        else:
            await self.audio.resume()
            button.textContent = "SOUND ON"
            button.setAttribute("aria-pressed", "true")

    def frame(self, timestamp):
        try:
            frame_seconds = (timestamp - self.last_time) / 1000 if self.last_time is not None else 0
            dt = min(.05, frame_seconds)
            self.last_time = timestamp
            if self.active:
                self.elapsed += dt
                k = self.keys
                self.player.angle += (("ArrowRight" in k) - ("ArrowLeft" in k)) * dt * 1.9
                forward = ("KeyW" in k or "ArrowUp" in k) - ("KeyS" in k or "ArrowDown" in k)
                strafe = ("KeyD" in k) - ("KeyA" in k)
                moving = self.player.move(self.room, forward, strafe, dt, "ShiftLeft" in k or "ShiftRight" in k)
                if moving:
                    self.bob += dt * 10
                self.swing = max(0, self.swing - dt)
                self.render(moving)
                self.frames += 1
                self.fps_time += frame_seconds
                if self.fps_time >= .5:
                    document.getElementById("fps").textContent = str(round(self.frames / self.fps_time))
                    self.frames, self.fps_time = 0, 0
                    angle = self.player.angle
                    document.getElementById("direction").textContent = ("E", "SE", "S", "SW", "W", "NW", "N", "NE")[round(angle / (math.pi / 4)) % 8]
                    if document.pointerLockElement == canvas:
                        self.note.textContent = "The gate is sealed. This is only the beginning." if self.player.y < 3.3 else "Explore the lower hall"
            js.requestAnimationFrame(self.frame_proxy)
        except Exception as error:
            self.pause()
            document.getElementById("status").textContent = f"The scene stopped: {error}. Reload to try again."
            raise

    def render(self, moving=False):
        p = self.player
        ca, sa = math.cos(p.angle), math.sin(p.angle)
        horizon = H / 2 + self.pitch + (math.sin(self.bob * 2) * 2 if moving else 0)
        ceiling = ctx.createLinearGradient(0, 0, 0, horizon)
        ceiling.addColorStop(0, "#0b100f")
        ceiling.addColorStop(1, "#242b25")
        ctx.fillStyle = ceiling
        ctx.fillRect(0, 0, W, H)
        floor = ctx.createLinearGradient(0, horizon, 0, H)
        floor.addColorStop(0, "#252b23")
        floor.addColorStop(.45, "#43483a")
        floor.addColorStop(1, "#62614b")
        ctx.fillStyle = floor
        ctx.fillRect(0, horizon, W, H - horizon)
        # Project actual world-space floor joints, so they remain anchored as you turn.
        ctx.save()
        ctx.beginPath()
        ctx.rect(0, horizon + 1, W, H - horizon)
        ctx.clip()
        ctx.strokeStyle = "#141e1b55"
        ctx.lineWidth = 1

        def grid_line(x1, y1, x2, y2):
            a = [(x1 - p.x) * -sa + (y1 - p.y) * ca, (x1 - p.x) * ca + (y1 - p.y) * sa]
            b = [(x2 - p.x) * -sa + (y2 - p.y) * ca, (x2 - p.x) * ca + (y2 - p.y) * sa]
            if a[1] < .1 and b[1] < .1:
                return
            if a[1] < .1:
                t = (.1 - a[1]) / (b[1] - a[1])
                a = [a[0] + t * (b[0] - a[0]), .1]
            if b[1] < .1:
                t = (.1 - b[1]) / (a[1] - b[1])
                b = [b[0] + t * (a[0] - b[0]), .1]
            ctx.beginPath()
            ctx.moveTo(W / 2 + a[0] * FOCAL / a[1], horizon + .5 * FOCAL / a[1])
            ctx.lineTo(W / 2 + b[0] * FOCAL / b[1], horizon + .5 * FOCAL / b[1])
            ctx.stroke()

        for x in range(self.room.width + 1):
            grid_line(x, 0, x, self.room.height)
        for y in range(self.room.height + 1):
            grid_line(0, y, self.room.width, y)
        ctx.restore()
        depths = []
        flicker = .025 * math.sin(self.elapsed * 8) + .014 * math.sin(self.elapsed * 17)
        for column in range(0, W, 2):
            camera_x = (2 * (column + 1) / W - 1) * FOV
            dx, dy = ca - sa * camera_x, sa + ca * camera_x
            distance, offset, material, side = self.room.cast(p.x, p.y, dx, dy)
            depths.append(distance)
            height = FOCAL / distance
            top = horizon - height * .5
            ctx.drawImage(self.textures[material], int(offset * 127), 0, 1, 128, column, top, 2, height)
            # Distance fog plus a small directional contrast to distinguish corners.
            dark = min(.90, .09 + distance * .052 + side * .13 - flicker)
            ctx.fillStyle = f"rgba(6,14,12,{dark:.3f})"
            ctx.fillRect(column, top, 2, height)
        # Billboards are sorted far-to-near and clipped against wall depth per strip.
        for x, y, kind in sorted(self.objects, key=lambda o: (o[0] - p.x) ** 2 + (o[1] - p.y) ** 2, reverse=True):
            dx, dy = x - p.x, y - p.y
            depth = dx * ca + dy * sa
            if depth <= .2:
                continue
            lateral = -dx * sa + dy * ca
            size = FOCAL / depth
            width = size * (.40 if kind == "torch" else .72)
            height = size * (.80 if kind == "torch" else .65)
            center = W / 2 + lateral * FOCAL / depth
            left = center - width / 2
            bottom = horizon + size * (.16 if kind == "torch" else .5)
            image = self.sprites[kind]
            ctx.globalAlpha = min(1, max(.3, 1 - depth * .035))
            for column in range(max(0, int(left) // 2 * 2), min(W, int(left + width) + 2), 2):
                if depth < depths[column // 2]:
                    source_x = max(0, min(95, (column - left) / width * 96))
                    ctx.drawImage(image, source_x, 0, min(96 - source_x, 192 / width), 128, column, bottom - height, 2, height)
            ctx.globalAlpha = 1
        self.draw_sword(moving)

    def draw_sword(self, moving):
        bob = math.sin(self.bob) * 4 if moving else math.sin(self.elapsed * 1.8) * 1.1
        progress = 1 - self.swing / .48 if self.swing else 0
        swing_arc = math.sin(progress * math.pi) if self.swing else 0
        ctx.save()
        ctx.translate(487 - swing_arc * 145, 370 + bob - swing_arc * 30)
        ctx.rotate(-.16 - swing_arc * 1.65)
        # Armored forearm and segmented gauntlet, viewed from the knight's eyes.
        polygon(ctx, [(3, 2), (42, -5), (76, 56), (14, 62), (-7, 29)], "#4f5955", "#171f20")
        polygon(ctx, [(12, 3), (34, -2), (60, 55), (34, 59)], "#818c80")
        for y in (12, 25, 38):
            polygon(ctx, [(-2 + y * .3, y), (42 + y * .45, y - 5), (48 + y * .45, y + 4), (y * .3, y + 10)], "#596760", "#27332e")
        # Leather grip, brass pommel and crossguard.
        polygon(ctx, [(-8, -65), (7, -65), (9, 2), (-9, 2)], "#392d23", "#161e1b")
        for y in range(-60, 0, 7):
            ctx.strokeStyle = "#89704d"
            ctx.beginPath()
            ctx.moveTo(-7, y)
            ctx.lineTo(7, y - 4)
            ctx.stroke()
        polygon(ctx, [(-10, -2), (9, -2), (13, 9), (0, 16), (-13, 8)], "#9b8b5d", "#d0bf83")
        polygon(ctx, [(-49, -72), (-39, -82), (-12, -73), (0, -80), (13, -73), (41, -82), (51, -73), (41, -65), (11, -65), (0, -60), (-13, -65), (-41, -65)], "#a49668", "#3e4132")
        polygon(ctx, [(-42, -75), (-13, -70), (0, -75), (13, -70), (43, -75), (40, -71), (0, -65)], "#d4c18a")
        # Long double-edged blade with a bright central ridge.
        polygon(ctx, [(-12, -78), (-10, -220), (0, -263), (11, -220), (13, -78), (0, -69)], "#8d9e98", "#283936")
        polygon(ctx, [(0, -258), (1, -80), (-10, -84), (-8, -220)], "#c3cec0")
        polygon(ctx, [(1, -250), (9, -219), (10, -84), (1, -80)], "#637d79")
        ctx.strokeStyle = "#edf0d4"
        ctx.beginPath()
        ctx.moveTo(0, -255)
        ctx.lineTo(0, -84)
        ctx.stroke()
        ctx.restore()


async def start():
    # Zapros delegates HTTP to browser fetch through its Pyodide handler.
    async with AsyncClient() as client:
        response = await client.get(str(js.URL.new("room.json", document.baseURI)))
        if response.status != 200:
            raise RuntimeError(f"Room request failed: HTTP {response.status}")
        data = response.json
    global game
    game = Game(data)
