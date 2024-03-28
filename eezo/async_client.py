from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .interface.interface import Message
from .connector import AsyncConnector

import asyncio
import aiohttp
import sys
import os

SERVER = "https://api-service-bofkvbi4va-ey.a.run.app"
if os.environ.get("EEZO_DEV_MODE") == "True":
    print("Running in dev mode")
    SERVER = "http://localhost:8082"

CREATE_MESSAGE_ENDPOINT = SERVER + "/v1/create-message/"
READ_MESSAGE_ENDPOINT = SERVER + "/v1/read-message/"
DELETE_MESSAGE_ENDPOINT = SERVER + "/v1/delete-message/"


class RestartHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            os.execl(sys.executable, sys.executable, *sys.argv)


class AsyncClient:
    def __init__(self, api_key=None, logger=False):
        self.connector_functions = {}
        self.tasks = []
        self.observer = Observer()
        self.api_key = os.environ["EEZO_API_KEY"] if api_key is None else api_key
        self.logger = logger
        if self.api_key is None:
            raise ValueError("Eezo api_key is required")

    def on(self, connector_id):
        def decorator(func):
            self.connector_functions[connector_id] = func
            return func

        return decorator

    async def connect(self):
        try:
            self.observer.schedule(RestartHandler(), ".", recursive=False)
            self.observer.start()

            for connector_id, func in self.connector_functions.items():
                c = AsyncConnector(self.api_key, connector_id, func, self.logger)
                task = asyncio.create_task(c.connect())
                self.tasks.append(task)

            await asyncio.gather(*self.tasks)

        except KeyboardInterrupt:
            for task in self.tasks:
                task.cancel()
            self.observer.stop()

    async def __request(self, method, endpoint, payload):
        async with aiohttp.ClientSession() as session:
            async with session.request(method, endpoint, json=payload) as response:
                response_json = await response.json()
                if response.status == 401:
                    raise Exception(f"Unauthorized. Probably invalid api_key")
                if response.status != 200:
                    raise Exception(
                        f"Error {response.status}: {response_json['detail']}"
                    )
                return response_json

    async def new_message(self, eezo_id, thread_id, context="direct_message"):
        new_message = Message()

        async def notify():
            nm = new_message.to_dict()
            await self.__request(
                "POST",
                CREATE_MESSAGE_ENDPOINT,
                {
                    "api_key": self.api_key,
                    "thread_id": thread_id,
                    "eezo_id": eezo_id,
                    "message_id": nm["id"],
                    "interface": nm["interface"],
                    "context": context,
                },
            )

        new_message.notify = notify
        return new_message

    async def delete_message(self, message_id):
        await self.__request(
            "POST",
            DELETE_MESSAGE_ENDPOINT,
            {"api_key": self.api_key, "message_id": message_id},
        )

    async def update_message(self, message_id):
        response_json = await self.__request(
            "POST",
            READ_MESSAGE_ENDPOINT,
            {"api_key": self.api_key, "message_id": message_id},
        )
        if "data" not in response_json:
            raise Exception(f"Message not found for id {message_id}")

        old_message = response_json["data"]
        new_message = Message()  # Assuming Message is refactored for async

        async def notify():
            nm = new_message.to_dict()
            await self.__request(
                "POST",
                CREATE_MESSAGE_ENDPOINT,
                {
                    "api_key": self.api_key,
                    "thread_id": old_message["thread_id"],
                    "eezo_id": old_message["eezo_id"],
                    "message_id": nm["id"],
                    "interface": nm["interface"],
                    # Find a way to get context from old_message_obj
                    "context": old_message["skill_id"],
                },
            )

        new_message.notify = notify
        new_message.id = old_message["id"]
        return new_message
