# Dungeon Knight

A small first-person fantasy RPG prototype: explore a torchlit stone hall as Sir Aldric, with an iron longsword in hand. The scene uses a classic DDA raycaster with procedural stone textures, depth-clipped props, distance fog, and a projected floor grid. No downloaded game artwork is required.

## Play locally

Requires Python 3.10+ and a modern desktop browser with keyboard and mouse.

```sh
python3 server.py
```

Open **http://127.0.0.1:8000**, wait for the runtime to load, and click **Enter the keep**. The first load needs internet access for Pyodide, the pinned Zapros package and its dependencies, and optional web fonts. The Python runtime is a substantial initial download; browser caching helps subsequent visits. Serve through HTTP; opening `index.html` directly will not work.

To use another port: `python3 server.py --port 8080`. To explicitly allow LAN access: `python3 server.py --host 0.0.0.0`.

| Control | Action |
| --- | --- |
| W / A / S / D | Walk / strafe |
| Mouse | Turn and look up/down while cursor is captured |
| Left / right arrows | Turn without mouse capture |
| Up / down arrows | Walk forward/backward |
| Shift | Run |
| Space / left click | Swing the sword |
| Escape | Pause and release cursor |
| Bottom-right expand button | Fullscreen |
| Sound button | Toggle a quiet ambient drone |

If the browser disallows cursor capture, use the arrow keys to turn. This initial prototype supports desktop controls; touch controls are not implemented. Sword swings are animated; combat, enemies, multiplayer, saves, and opening the gate are future work. Health and level are character presentation for this scene.

## Architecture

- `server.py`: Python standard-library static HTTP server, bound to localhost by default. No pip installation needed on the host.
- `web/boot.js`: loads pinned Pyodide and installs `zapros==0.19.0`, then starts Python. This is the only JavaScript application file; it contains no game logic.
- `web/core.py`: pure Python DDA raycasting, player movement, and wall collision.
- `web/game.py`: Python Canvas 2D renderer, procedural textures and props, sword animation, input, audio, and game loop.
- `web/room.json`: editable room layout, materials, spawn point, and prop positions. `0` is open space; `1` stone, `2` a sealed wooden gate, `3` mossy stone. Keep the perimeter closed and the spawn in open space.

Zapros is an **HTTP client**, so it loads the room JSON in the browser using its [official Pyodide support](https://zapros.dev/browser). The standard library handles serving files. Python runs locally in each browser through [Pyodide](https://pyodide.org/en/stable/usage/quickstart.html); there is no per-frame network round trip.

## Checks

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q server.py web tests
```
