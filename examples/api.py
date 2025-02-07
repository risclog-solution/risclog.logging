import asyncio
import logging

from fastapi import FastAPI
from risclog.logging import getLogger, log_decorator

app = FastAPI()
logger = getLogger(__name__)
logger.add_file_handler(
    'myfastapi.log', level=logging.DEBUG
)  # File-Log, farblos
logger.set_level(logging.DEBUG)


@app.get('/')
def hello_world():
    logger.info('Hello World called')
    return {'message': 'Hello World'}


@app.get('/compute_sync')
def compute_sync(a: int, b: int):
    logger.info('compute_sync called', a=a, b=b)
    return {'result': a + b}


@app.get('/compute_async')
async def compute_async(a: int, b: int):
    logger.info('compute_async called', a=a, b=b)
    await asyncio.sleep(1)
    return {'result': a + b}


@app.get('/info_async')
async def info_async():
    await logger.info('Logging async from info_async')
    return {'message': 'ok'}


@log_decorator
def sum_args(a, b):
    return a + b


@app.get('/compute_sync_deco')
@log_decorator
def compute_sync_deco(a: int, b: int):
    logger.info('compute_sync_deco called', a=a, b=b)
    sum_args(a, b)


@app.get('/compute_async_deco')
@log_decorator
async def compute_async_deco(a: int, b: int):
    await asyncio.sleep(1)
    return a + b
