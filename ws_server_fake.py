"""
Simple WebSocket broadcaster for testing the browser client.
Run this to emit random 'hand landmarks' so the web particle system can follow them.
Install dependency: pip install websockets

Usage:
    python ws_server_fake.py

Connects on ws://0.0.0.0:8765 and broadcasts random landmarks at ~20Hz.
"""

import asyncio
import json
import random

import websockets

CLIENTS = set()


async def handler(ws, path=None):
    # websockets library changed handler signature across versions
    # accept either (ws, path) or just (ws,) by making path optional
    CLIENTS.add(ws)
    try:
        await ws.wait_closed()
    finally:
        CLIENTS.discard(ws)


async def broadcaster():
    while True:
        if CLIENTS:
            landmarks = []
                # generate 1-2 fake hands, each with 21 landmarks and handedness
                hands = []
                hand_count = random.choice([1, 2])
                for h in range(hand_count):
                    landmarks = []
                    for i in range(21):
                        landmarks.append({
                            'x': random.random(),
                            'y': random.random(),
                            'z': random.random() * 0.2,
                        })
                    handedness = 'Left' if h == 0 else 'Right'
                    hands.append({'landmarks': landmarks, 'handedness': handedness})
                msg = json.dumps({'hands': hands, 'detected': True})
            # send concurrently and ignore individual send errors
            await asyncio.gather(
                *(c.send(msg) for c in list(CLIENTS)), return_exceptions=True
            )
        await asyncio.sleep(0.05)


async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("WS test server listening on ws://0.0.0.0:8765")
    await broadcaster()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped")
