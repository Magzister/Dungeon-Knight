"""Serve the local game. No server dependencies are required."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Dungeon Knight development server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    handler = partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "web"))
    with ThreadingHTTPServer((args.host, args.port), handler) as server:
        print(f"Dungeon Knight: http://{args.host}:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nLeaving the dungeon.")


if __name__ == "__main__":
    main()
