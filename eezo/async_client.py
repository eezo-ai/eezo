from .errors import AuthorizationError, RequestError, ResourceNotFoundError
from typing import Optional, Callable, Dict, List, Any
from watchdog.events import FileSystemEventHandler
from .interface.interface import Message
from watchdog.observers import Observer
from .connector import AsyncConnector
from .agent import Agents, Agent

import requests
import asyncio
import httpx
import sys
import os

from .state_async import StateProxyAsync

SERVER = "https://api-service-bofkvbi4va-ey.a.run.app"
if os.environ.get("EEZO_DEV_MODE") == "True":
    print("Running in dev mode")
    SERVER = "http://localhost:8082"

AUTH_URL = SERVER + "/v1/signin/"

CREATE_MESSAGE_ENDPOINT = SERVER + "/v1/create-message/"
READ_MESSAGE_ENDPOINT = SERVER + "/v1/read-message/"
DELETE_MESSAGE_ENDPOINT = SERVER + "/v1/delete-message/"

CREATE_STATE_ENDPOINT = SERVER + "/v1/create-state/"
READ_STATE_ENDPOINT = SERVER + "/v1/read-state/"
UPDATE_STATE_ENDPOINT = SERVER + "/v1/update-state/"

GET_AGENTS_ENDPOINT = SERVER + "/v1/get-agents/"
GET_AGENT_ENDPOINT = SERVER + "/v1/get-agent/"


class RestartHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            os.execl(sys.executable, sys.executable, *sys.argv)


class AsyncClient:

    def __init__(self, api_key: Optional[str] = None, logger: bool = False) -> None:
        """Initialize the Client with an optional API key and a logger flag.

        Args:
            api_key (Optional[str]): The API key for authentication. If None, it defaults to the EEZO_API_KEY environment variable.
            logger (bool): Flag to enable logging.

        Raises:
            ValueError: If api_key is None after checking the environment.
        """
        self.connector_functions: Dict[str, Callable] = {}
        self.tasks: List[asyncio.Task] = []
        self.observer = Observer()
        self.api_key: str = (
            api_key if api_key is not None else os.getenv("EEZO_API_KEY")
        )
        self.logger: bool = logger
        self.state_was_loaded = False
        self.user_id: Optional[str] = None
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient()

        if not self.api_key:
            raise ValueError("Eezo api_key is required")

        self._state_proxy: StateProxyAsync = StateProxyAsync(self)

        result = requests.post(AUTH_URL, json={"api_key": self.api_key})
        result.raise_for_status()
        result_json = result.json()
        self.user_id = result_json["user_id"]
        self.token = result_json["token"]

    def on(self, connector_id: str) -> Callable:
        """Decorator to register a connector function.

        Args:
            connector_id (str): The identifier for the connector.

        Returns:
            Callable: The decorator function.
        """

        def decorator(func: Callable) -> Callable:
            if not callable(func):
                raise TypeError("Function must be callable")
            self.connector_functions[connector_id] = func
            return func

        return decorator

    async def connect(self) -> None:
        """Connect to the Eezo server and start the client. This involves scheduling
        tasks in a thread pool executor and handling responses."""
        try:
            self.observer.schedule(RestartHandler(), ".", recursive=False)
            self.observer.start()

            for connector_id, func in self.connector_functions.items():
                c = AsyncConnector(self.api_key, connector_id, func, self.logger)
                await c.authenticate()
                task = asyncio.create_task(c.connect())
                self.tasks.append(task)

            await asyncio.gather(*self.tasks)

        except KeyboardInterrupt:
            pass
        finally:
            for task in self.tasks:
                task.cancel()
            self.observer.stop()

    async def _request(
        self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Makes an asynchronous HTTP request to a specified endpoint with a given payload.

        Args:
            method (str): The HTTP method to use (e.g., 'GET', 'POST').
            endpoint (str): The URL endpoint to send the request to.
            payload (Optional[Dict[str, Any]]): The payload to send with the request. Defaults to None.

        Returns:
            Dict[str, Any]: The JSON response parsed into a dictionary.

        Raises:
            AuthorizationError, ResourceNotFoundError, RequestError: Specific errors based on the HTTP response.

        This method includes error handling for common HTTP errors and ensures that the API key is included in every request.
        """
        if payload is None:
            payload = {}
        payload["api_key"] = self.api_key
        try:
            response = await self.client.request(method, endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [401, 403]:
                raise AuthorizationError(
                    "Authorization error. Check your API key."
                ) from e
            elif e.response.status_code == 404:
                if endpoint in {READ_STATE_ENDPOINT, UPDATE_STATE_ENDPOINT}:
                    return await self.create_state(self.user_id, {})
                else:
                    raise ResourceNotFoundError(f"Not found: {endpoint}") from e
            else:
                raise RequestError(f"Unexpected error: {e.response.text}") from e

    async def new_message(
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
        new_message = Message()

        async def notify():
            nm = new_message.to_dict()
            await self._request(
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

    async def delete_message(self, message_id: str) -> None:
        """Delete a message by its ID.

        Args:
            message_id (str): The ID of the message to delete.
        """
        await self._request(
            "POST",
            DELETE_MESSAGE_ENDPOINT,
            {"api_key": self.api_key, "message_id": message_id},
        )

    async def update_message(self, message_id: str) -> Message:
        """Update a message by its ID and return the updated message object.

        Args:
            message_id (str): The ID of the message to update.

        Returns:
            Message: The updated message object.

        Raises:
            Exception: If the message with the given ID is not found.
        """
        response_json = await self._request(
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
            await self._request(
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

    async def get_agents(self, online_only: bool = False) -> Agents:
        """Retrieve and return a list of all agents.

        Args:
            online_only (bool): Flag to filter agents that are online.

        Returns:
            Agents: A list of agents.
        """
        response = await self._request(
            "POST", GET_AGENTS_ENDPOINT, {"api_key": self.api_key}
        )
        agents_dict = response["data"]
        agents = Agents(agents_dict)
        if online_only:
            agents.agents = [agent for agent in agents.agents if agent.is_online()]

        return agents

    async def get_agent(self, agent_id: str) -> Agent:
        """Retrieve and return an agent by its ID.

        Args:
            agent_id (str): The ID of the agent to retrieve.

        Returns:
            Agent: The agent object.

        Raises:
            Exception: If the agent with the given ID is not found.
        """
        response = await self._request(
            "POST", GET_AGENT_ENDPOINT, {"api_key": self.api_key, "agent_id": agent_id}
        )
        agent_dict = response["data"]
        return Agent(**agent_dict)

    async def create_state(
        self, state_id: str, state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Creates or initializes a state for a given ID.

        Args:
            state_id (str): The identifier of the state to create or initialize.
            state (Optional[Dict[str, Any]]): The initial state data. Defaults to an empty dictionary if None.

        Returns:
            Dict[str, Any]: The state as stored after creation or initialization.

        This method handles the creation of a new state via a POST request, ensuring any initial data is set as specified.
        """
        if state is None:
            state = {}
        result = await self._request(
            "POST", CREATE_STATE_ENDPOINT, {"state_id": state_id, "state": state}
        )
        return result.get("data", {}).get("state", {})

    async def read_state(self, state_id: str) -> Dict[str, Any]:
        """
        Reads the state associated with a given state ID.

        Args:
            state_id (str): The identifier of the state to be read.

        Returns:
            Dict[str, Any]: The state data associated with the state ID.

        This method retrieves the current state data for the specified ID via a POST request.
        """
        result = await self._request(
            "POST", READ_STATE_ENDPOINT, {"state_id": state_id}
        )
        return result.get("data", {}).get("state", {})

    async def update_state(
        self, state_id: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Updates the state associated with a given state ID with new data.

        Args:
            state_id (str): The identifier of the state to update.
            state (Dict[str, Any]): The new data to update the state with.

        Returns:
            Dict[str, Any]: The updated state data.

        This method handles the updating of a state via a POST request, applying the new state data as specified.
        """
        result = await self._request(
            "POST", UPDATE_STATE_ENDPOINT, {"state_id": state_id, "state": state}
        )
        return result.get("data", {}).get("state", {})

    @property
    def state(self):
        """
        Provides access to the state proxy associated with this client.

        Returns:
            StateProxy: The state proxy managing the state data.

        This property allows direct access to the state management functionalities provided by the StateProxy instance.
        """
        return self._state_proxy

    async def load_state(self):
        """
        Asynchronously loads the state using the state proxy.

        This method initiates the loading of the state data through the state proxy, which handles the asynchronous operation.
        """
        await self._state_proxy.load()

    async def save_state(self):
        """
        Asynchronously saves the state using the state proxy.

        This method initiates the saving of the state data through the state proxy, which manages the asynchronous operation.
        """
        await self._state_proxy.save()
