import asyncio
import logging

from fastapi import FastAPI
from risclog.logging import getLogger, log_decorator

app = FastAPI()
logger = getLogger(__name__)
logger.add_file_handler("myfastapi.log", level=logging.DEBUG)  # File-Log, farblos

# Füge einen Console Handler für Decorator Logs hinzu
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

logger.set_level(logging.DEBUG)


@app.get("/")
def hello_world():
    logger.info("Hello World called")
    return {"message": "Hello World"}


@app.get("/compute_sync")
def compute_sync(a: int, b: int):
    logger.info("compute_sync called", a=a, b=b)
    return {"result": a + b}


@app.get("/compute_async")
async def compute_async(a: int, b: int):
    logger.info("compute_async called", a=a, b=b)
    await asyncio.sleep(1)
    return {"result": a + b}


@app.get("/info_async")
async def info_async():
    await logger.info("Logging async from info_async")
    return {"message": "ok"}


@log_decorator
def sum_args(a, b):
    return a + b


@app.get("/compute_sync_deco")
@log_decorator
def compute_sync_deco(a: int, b: int):
    logger.info("compute_sync_deco called", a=a, b=b)
    sum_args(a, b)


@app.get("/compute_async_deco")
@log_decorator
async def compute_async_deco(a: int, b: int):
    await asyncio.sleep(1)
    return a + b


if __name__ == "__main__":
    import time
    import requests
    import uvicorn
    from threading import Thread

    # Starte den Server in einem separaten Thread
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()

    # Warte kurz bis der Server startet
    time.sleep(2)

    print("=== API Endpoint Tests ===\n")

    base_url = "http://127.0.0.1:8000"

    try:
        # Test 1: Hello World
        print("Test 1: GET /")
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")

        # Test 2: Sync Berechnung
        print("Test 2: GET /compute_sync?a=5&b=3")
        response = requests.get(f"{base_url}/compute_sync", params={"a": 5, "b": 3})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")

        # Test 3: Async Berechnung
        print("Test 3: GET /compute_async?a=10&b=20")
        response = requests.get(f"{base_url}/compute_async", params={"a": 10, "b": 20})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")

        # Test 4: Info Async
        print("Test 4: GET /info_async")
        response = requests.get(f"{base_url}/info_async")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")

        # Test 5: Sync mit Decorator
        print("Test 5: GET /compute_sync_deco?a=7&b=8")
        response = requests.get(
            f"{base_url}/compute_sync_deco", params={"a": 7, "b": 8}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")

        # Test 6: Async mit Decorator
        print("Test 6: GET /compute_async_deco?a=15&b=25")
        response = requests.get(
            f"{base_url}/compute_async_deco", params={"a": 15, "b": 25}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")

        print("✓ Alle Tests abgeschlossen!")
        print("Logfile: myfastapi.log")

    except Exception as e:
        print(f"❌ Error: {e}")
