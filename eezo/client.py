from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .interface.interface import Message
from .connector import Connector

import concurrent.futures
import requests
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


class Client:
    def __init__(self, api_key=None, logger=False):
        self.connector_functions = {}
        self.futures = []
        self.executor = concurrent.futures.ThreadPoolExecutor()
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

    def connect(self):
        try:
            self.observer.schedule(RestartHandler(), ".", recursive=False)
            self.observer.start()
            self.futures = []
            for connector_id, func in self.connector_functions.items():
                c = Connector(self.api_key, connector_id, func, self.logger)
                self.futures.append(self.executor.submit(c.connect))

            for future in self.futures:
                future.result()

        except KeyboardInterrupt:
            for future in self.futures:
                future.cancel()
            self.executor.shutdown(wait=False)
            self.observer.stop()

    def __request(self, method, endpoint, payload):
        response = requests.request(method, endpoint, json=payload)
        if response.status_code == 401:
            raise Exception(f"Unauthorized. Probably invalid api_key")
        if response.status_code != 200:
            raise Exception(
                f"Error {response.status_code}: {response.json()['detail']}"
            )
        return response

    def new_message(self, eezo_id, thread_id, context="direct_message"):
        new_message = None

        def notify():
            messgage_obj = new_message.to_dict()
            self.__request(
                "POST",
                CREATE_MESSAGE_ENDPOINT,
                {
                    "api_key": self.api_key,
                    "thread_id": thread_id,
                    "eezo_id": eezo_id,
                    "message_id": messgage_obj["id"],
                    "interface": messgage_obj["interface"],
                    "context": context,
                },
            )

        new_message = Message(notify=notify)
        return new_message

    def delete_message(self, message_id):
        self.__request(
            "POST",
            DELETE_MESSAGE_ENDPOINT,
            {
                "api_key": self.api_key,
                "message_id": message_id,
            },
        )

    def update_message(self, message_id):
        response = self.__request(
            "POST",
            READ_MESSAGE_ENDPOINT,
            {
                "api_key": self.api_key,
                "message_id": message_id,
            },
        )

        if "data" not in response.json():
            raise Exception(f"Message not found for id {message_id}")
        old_message_obj = response.json()["data"]

        new_message = None

        def notify():
            messgage_obj = new_message.to_dict()
            self.__request(
                "POST",
                CREATE_MESSAGE_ENDPOINT,
                {
                    "api_key": self.api_key,
                    "thread_id": old_message_obj["thread_id"],
                    "eezo_id": old_message_obj["eezo_id"],
                    "message_id": messgage_obj["id"],
                    "interface": messgage_obj["interface"],
                    # Find a way to get context from old_message_obj
                    "context": old_message_obj["skill_id"],
                },
            )

        new_message = Message(notify=notify)
        new_message.id = old_message_obj["id"]
        return new_message
