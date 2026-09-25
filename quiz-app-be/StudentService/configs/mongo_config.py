import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from umongo.frameworks import MotorAsyncIOInstance


def get_umongo_instance(mongo_uri: str, db_name: str):

    motor_client = AsyncIOMotorClient(mongo_uri)[db_name]
    motor_client.get_io_loop = asyncio.get_running_loop
    instance = MotorAsyncIOInstance(motor_client)
    return instance