from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from typing import Optional, Callable, Dict, List
from .interface.interface import Message
from .connector import Connector
from .agent import Agents, Agent

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

GET_AGENTS_ENDPOINT = SERVER + "/v1/get-agents/"
GET_AGENT_ENDPOINT = SERVER + "/v1/get-agent/"


class RestartHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            os.execl(sys.executable, sys.executable, *sys.argv)


class Client:
    def __init__(self, api_key: Optional[str] = None, logger: bool = False) -> None:
        """Initialize the Client with an optional API key and a logger flag.

        Args:
            api_key (Optional[str]): The API key for authentication. If None, it defaults to the EEZO_API_KEY environment variable.
            logger (bool): Flag to enable logging.

        Raises:
            ValueError: If api_key is None after checking the environment.
        """
        self.connector_functions: Dict[str, Callable] = {}
        self.futures: List[concurrent.futures.Future] = []
        self.executor: concurrent.futures.ThreadPoolExecutor = (
            concurrent.futures.ThreadPoolExecutor()
        )
        self.observer = Observer()
        self.api_key: str = (
            api_key if api_key is not None else os.getenv("EEZO_API_KEY")
        )
        self.logger: bool = logger
        if not self.api_key:
            raise ValueError("Eezo api_key is required")

    def on(self, connector_id: str) -> Callable:
        """Decorator to register a connector function.

        Args:
            connector_id (str): The identifier for the connector.

        Returns:
            Callable: The decorator function.
        """

        def decorator(func: Callable) -> Callable:
            if not callable(func):
                raise TypeError(f"Expected a callable, got {type(func)} instead")
            self.connector_functions[connector_id] = func
            return func

        return decorator

    def connect(self) -> None:
        """Connect to the Eezo server and start the client. This involves scheduling
        tasks in a thread pool executor and handling responses."""
        try:
            self.observer.schedule(RestartHandler(), ".", recursive=False)
            self.observer.start()
            self.futures = []
            self.job_responses: Dict[str, str] = {}

            for connector_id, func in self.connector_functions.items():
                c = Connector(
                    self.api_key, connector_id, func, self.job_responses, self.logger
                )
                self.futures.append(self.executor.submit(c.connect))

            for future in self.futures:
                future.result()

        except KeyboardInterrupt:
            pass
        finally:
            for future in self.futures:
                future.cancel()
            self.executor.shutdown(wait=False)
            self.observer.stop()

    def __request(self, method: str, endpoint: str, payload: Dict) -> requests.Response:
        """Make an HTTP request with specified method, endpoint, and payload.

        Args:
            method (str): The HTTP method.
            endpoint (str): The API endpoint.
            payload (Dict): The payload for the request.

        Returns:
            requests.Response: The response from the server.

        Raises:
            Exception: If the response status is unauthorized or an error occurred.
        """
        try:
            response = requests.request(method, endpoint, json=payload)
            if response.status_code == 401:
                raise Exception(f"Unauthorized. Probably invalid api_key")
            if response.status_code != 200:
                raise Exception(
                    f"Error {response.status_code}: {response.json()['detail']}"
                )
            return response
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Request failed: {str(e)}")

    def new_message(
        self, eezo_id: str, thread_id: str, context: str = "direct_message"
    ) -> Message:
        """Create and return a new message object configured to notify on updates.

        Args:
            eezo_id (str): The Eezo user identifier.
            thread_id (str): The thread identifier where the message belongs.
            context (str): The context of the message, defaults to 'direct_message'.

        Returns:
            Message: The newly created message object.
        """
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

    def delete_message(self, message_id: str) -> None:
        """Delete a message by its ID.

        Args:
            message_id (str): The ID of the message to delete.
        """
        self.__request(
            "POST",
            DELETE_MESSAGE_ENDPOINT,
            {
                "api_key": self.api_key,
                "message_id": message_id,
            },
        )

    def update_message(self, message_id: str) -> Message:
        """Update a message by its ID and return the updated message object.

        Args:
            message_id (str): The ID of the message to update.

        Returns:
            Message: The updated message object.

        Raises:
            Exception: If the message with the given ID is not found.
        """
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

    def get_agents(self, online_only: bool = False) -> Agents:
        """Retrieve and return a list of all agents.

        Args:
            online_only (bool): Flag to filter agents that are online.

        Returns:
            Agents: A list of agents.
        """
        response = self.__request(
            "POST", GET_AGENTS_ENDPOINT, {"api_key": self.api_key}
        )
        agents_dict = response.json()["data"]
        agents = Agents(agents_dict)
        if online_only:
            agents.agents = [agent for agent in agents.agents if agent.is_online()]

        return agents

    def get_agent(self, agent_id: str) -> Agent:
        """Retrieve and return an agent by its ID.

        Args:
            agent_id (str): The ID of the agent to retrieve.

        Returns:
            Agent: The agent object.

        Raises:
            Exception: If the agent with the given ID is not found.
        """
        response = self.__request(
            "POST", GET_AGENT_ENDPOINT, {"api_key": self.api_key, "agent_id": agent_id}
        )
        agent_dict = response.json()["data"]
        return Agents([agent_dict]).agents[0]
