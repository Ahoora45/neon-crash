import asyncio
import random
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

app = FastAPI()

clients = set()
round_number = 0


async def broadcast(data):
    disconnected = set()

    for client in clients:
        try:
            await client.send_json(data)
        except Exception:
            disconnected.add(client)

    for client in disconnected:
        clients.discard(client)


def calculate_multiplier(elapsed):
    # رشد نرم و تدریجی ضریب
    return 1.0 + (elapsed * 0.12) + (elapsed ** 1.45) * 0.018


async def game_loop():
    global round_number

    while True:
        round_number += 1

        # مرحله آماده‌سازی: 5 ثانیه
        for remaining in range(5, 0, -1):
            await broadcast({
                "type": "state",
                "phase": "betting",
                "seconds_left": remaining,
                "multiplier": 1.00,
                "round": round_number
            })
            await asyncio.sleep(1)

        # ضریب انفجار این دور
        crash_at = round(random.uniform(1.50, 8.00), 2)

        start_time = time.monotonic()

        # شروع دور
        while True:
            elapsed = time.monotonic() - start_time
            multiplier = calculate_multiplier(elapsed)

            if multiplier >= crash_at:
                multiplier = crash_at

                await broadcast({
                    "type": "crash",
                    "phase": "crashed",
                    "multiplier": round(multiplier, 2),
                    "round": round_number
                })

                break

            await broadcast({
                "type": "state",
                "phase": "running",
                "multiplier": round(multiplier, 2),
                "round": round_number
            })

            await asyncio.sleep(0.05)

        # کمی مکث قبل از دور بعد
        await asyncio.sleep(1)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(game_loop())


@app.get("/")
async def home():
    return JSONResponse({
        "status": "online",
        "game": "NEON CRASH"
    })


@app.get("/health")
async def health():
    return {"ok": True}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        clients.discard(websocket)

    except Exception:
        clients.discard(websocket)
