from .errors import AuthorizationError, ResourceNotFoundError, RequestError
from typing import Any, Dict, Callable, Optional, Iterator
from .message import Message

import httpx
import logging
import uuid
import os


SERVER = "https://api-service-bofkvbi4va-ey.a.run.app"
if os.environ.get("EEZO_DEV_MODE") == "True":
    print("Running in dev mode")
    SERVER = "http://localhost:8082"

CREATE_STATE_ENDPOINT = SERVER + "/v1/create-state/"
READ_STATE_ENDPOINT = SERVER + "/v1/read-state/"
UPDATE_STATE_ENDPOINT = SERVER + "/v1/update-state/"


class StateProxy:
    """
    Proxy class for managing the state data associated with a user session in an asynchronous context.

    This class provides a dictionary-like interface to the state, allowing items
    to be accessed, set, or deleted. It also handles asynchronously loading and saving the state
    through the associated interface.

    Attributes:
        interface: The asynchronous Interface instance that this proxy is managing state for.
        _state: A dictionary that holds the state data.
    """

    def __init__(self, interface: "AsyncInterface") -> None:
        """
        Initialize the StateProxy instance for asynchronous operations.

        Args:
            interface: The asynchronous Interface instance that this proxy is managing state for.
        """
        self.interface = interface
        self._state: Dict[str, Any] = {}

    async def load(self) -> None:
        """
        Asynchronously load the state data from the interface using the configured user ID.

        If state data is loaded successfully, it's set to the local state and the interface
        is notified that the state was loaded. Otherwise, logs an error message.
        """
        logging.info("<< Loading state")
        result: Dict[str, Any] = await self.interface.read_state(self.interface.user_id)
        if result is not None:
            self._state = result
            self.interface.state_was_loaded = True
        else:
            logging.error("Failed to load state.")

    def __getitem__(self, key: str) -> Any:
        """Get an item from the state by key."""
        return self._state.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item in the state."""
        self._state[key] = value

    def __delitem__(self, key: str) -> None:
        """Remove an item from the state by key if it exists."""
        if key in self._state:
            del self._state[key]

    def __str__(self) -> str:
        """Return the string representation of the state."""
        return str(self._state)

    def __repr__(self) -> str:
        """Return the official string representation of the StateProxy instance."""
        return f"StateProxy({repr(self._state)})"

    def items(self) -> Dict[str, Any].items:
        """Return a view of the state's items."""
        return self._state.items()

    def keys(self) -> Dict[str, Any].keys:
        """Return a view of the state's keys."""
        return self._state.keys()

    def values(self) -> Dict[str, Any].values:
        """Return a view of the state's values."""
        return self._state.values()

    def __iter__(self) -> Iterator[str]:
        """Return an iterator over the state's keys."""
        return iter(self._state)

    def __len__(self) -> int:
        """Return the number of items in the state."""
        return len(self._state)

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for key if key is in the state, else default."""
        return self._state.get(key, default)

    async def save(self) -> None:
        """
        Asynchronously save the state data to the interface.

        If the state was loaded and is not empty, the state is asynchronously updated through the
        interface using the configured user ID. If the state was not loaded, it logs a warning.
        """
        logging.info(">> Saving state")
        if not self.interface.state_was_loaded:
            logging.warning("State was not loaded, skipping save.")
        elif self._state:
            await self.interface.update_state(self.interface.user_id, self._state)
        else:
            logging.info("State is empty, nothing to save.")


class AsyncInterface:
    def __init__(
        self,
        job_id: str,
        user_id: str,
        api_key: str,
        cb_send_message: Callable[[Dict[str, Any]], Any],
        cb_invoke_connector: Callable[[Dict[str, Any]], Any],
        cb_get_result: Callable[[str], Any],
    ):
        """
        Initializes the AsyncInterface with essential identifiers and callback functions.

        Args:
            job_id (str): A unique identifier for the job associated with this interface.
            user_id (str): The user ID associated with this interface for managing user-specific data.
            api_key (str): The API key used for authenticating requests made by this interface.
            cb_send_message (Callable): A callback function that sends messages based on provided data.
            cb_invoke_connector (Callable): A callback function to initiate tasks or actions with external services.
            cb_get_result (Callable): A callback function to fetch results of the invoked tasks or actions.

        The AsyncInterface manages asynchronous interactions with backend services, handling state, messaging,
        and external service invocations.
        """
        self.job_id: str = job_id
        self.message: Optional[Message] = None
        self.user_id: str = user_id
        self.api_key: str = api_key
        self.send_message: Callable[[Dict[str, Any]], Any] = cb_send_message
        self.invoke_connector: Callable[[Dict[str, Any]], Any] = cb_invoke_connector
        self.get_result: Callable[[str], Any] = cb_get_result
        self._state_proxy: StateProxy = StateProxy(self)
        self.client: httpx.AsyncClient = httpx.AsyncClient()
        self.state_was_loaded: bool = False

    def new_message(self) -> Message:
        """
        Creates a new Message object with an associated notification callback.

        Returns:
            Message: The newly created Message object, ready to be filled with content and sent.

        This method initializes a Message object that includes a notification mechanism when the message needs to be sent.
        """
        self.message = Message(notify=self.notify)
        return self.message

    async def notify(self) -> None:
        """
        Asynchronously sends a notification that the message is ready.

        Raises:
            Exception: If no message has been created before calling this method.

        This method checks if a message has been created and configured, then uses the provided send_message callback
        to send the message data to an external service or another component of the application.
        """
        if self.message is None:
            raise Exception("Please create a message first")
        message_obj = self.message.to_dict()
        await self.send_message(
            {
                "message_id": message_obj["id"],
                "interface": message_obj["interface"],
            }
        )

    async def _run(self, skill_id: str, **kwargs: Any) -> Any:
        """
        Generic method to run a job with the specified skill identifier and additional keyword arguments.

        Args:
            skill_id (str): The identifier of the skill or task to be executed.
            **kwargs (Any): Additional keyword arguments passed to the skill execution logic.

        Returns:
            Any: The result of the skill execution, fetched using the get_result callback.

        Raises:
            ValueError: If the skill_id is not provided.

        This method manages the creation of a new job, invokes the connector callback to execute the job,
        and retrieves the results using the get_result callback.
        """
        if not skill_id:
            raise ValueError("skill_id is required")

        job_id = str(uuid.uuid4())
        await self.invoke_connector(
            {
                "new_job_id": job_id,
                "skill_id": skill_id,
                "skill_payload": kwargs,
            }
        )
        return await self.get_result(job_id)

    async def get_thread(self, nr: int = 5, to_string: bool = False) -> Any:
        """
        Retrieves a thread of messages or data, specified by its length and format.

        Args:
            nr (int): Number of items in the thread to retrieve. Defaults to 5.
            to_string (bool): Whether to convert the thread to string format. Defaults to False.

        Returns:
            Any: The thread of messages or data as specified by the parameters.

        This method is a specialized usage of the _run method to fetch threads, passing specific arguments to it.
        """
        return await self._run(
            skill_id="s_get_thread", nr_of_messages=nr, to_string=to_string
        )

    async def invoke(self, agent_id: str, **kwargs: Any) -> Any:
        """
        Invokes an agent or a service with specified parameters.

        Args:
            agent_id (str): The identifier of the agent or service to be invoked.
            **kwargs (Any): Additional parameters to pass to the agent or service.

        Returns:
            Any: The result of the agent or service invocation.

        This method facilitates the invocation of agents or services, using the _run method to handle the operation.
        """
        return await self._run(skill_id=agent_id, **kwargs)

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
        Provides access to the state proxy associated with this interface.

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
