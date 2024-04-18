from .errors import AuthorizationError, ResourceNotFoundError, RequestError
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from .message import Message
from typing import Any, Dict, Callable, Optional, Iterator


import requests
import logging
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
    Proxy class for managing the state data associated with a user session.

    This class provides a dictionary-like interface to the state, allowing items
    to be accessed, set, or deleted. It also handles loading and saving the state
    through the associated interface.

    Attributes:
        interface: The Interface instance that this proxy is managing state for.
        _state: A dictionary that holds the state data.
    """

    def __init__(self, interface: "Interface") -> None:
        """
        Initialize the StateProxy instance.

        Args:
            interface: The Interface instance that this proxy is managing state for.
        """
        self.interface: Interface = interface
        self._state: Dict[str, Any] = {}

    def load(self) -> None:
        """
        Load the state data from the interface using the configured user ID.

        If state data is loaded successfully, it's set to the local state and the interface
        is notified that the state was loaded. Otherwise, logs an error message.
        """
        logging.info("<< Loading state")
        result = self.interface.read_state(self.interface.user_id)
        if result is not None:
            self._state = result
            self.interface.state_was_loaded = True
        else:
            logging.error("Failed to load state.")

    def __getitem__(self, key: str) -> Any:
        """Get an item from the state by key."""
        return self._state.get(key, None)

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
        state_loaded = self.interface.state_was_loaded
        return f"StateProxy(state={repr(self._state)}, state_was_loaded={state_loaded})"

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

    def save(self) -> None:
        """
        Save the state data to the interface.

        If the state was loaded, the state is updated through the interface using
        the configured user ID. If the state was not loaded, it logs a warning.
        """
        logging.info(">> Saving state")
        if not self.interface.state_was_loaded:
            logging.warning("State was not loaded, skipping save.")
            return

        self.interface.update_state(self.interface.user_id, self._state)


class Interface:
    """
    Interface class for managing communications and state for a specific job identified by a job ID.

    Attributes:
        job_id: Identifier for the specific job this interface is associated with.
        user_id: User identifier for state and message association.
        api_key: API key for authorization purposes.
        send_message: Callback function to send messages.
        _run: Private callback function to execute skills or agents.
        _state_proxy: Instance of StateProxy for managing the state.
        state_was_loaded: Flag indicating if the state has been loaded.
        session: Requests session for HTTP communication with retry logic.
    """

    def __init__(
        self,
        job_id: str,
        user_id: str,
        api_key: str,
        cb_send_message: Callable[[Dict[str, Any]], Any],
        cb_run: Callable[..., Any],
    ):
        """
        Initialize the Interface with identifiers and callback functions.

        Args:
            job_id: A unique identifier for the job to which this interface pertains.
            user_id: A unique identifier for the user who is associated with this job.
            api_key: A string that represents the API key for authentication.
            cb_send_message: A callback function that is used to send messages.
            cb_run: A callback function that is used to execute agents or skills.

        The Interface class acts as a facilitator between the client's job-specific operations and the server's
        state management and messaging systems. It encapsulates methods for message creation, notification,
        state retrieval, and invocation of external skills or agents.
        """
        self.job_id = job_id
        self.message: Optional[Message] = None
        self.user_id = user_id
        self.api_key = api_key
        self.send_message = cb_send_message
        self._run = cb_run
        self._state_proxy = StateProxy(self)
        self.state_was_loaded = False

        self.session = self._configure_session()

    @staticmethod
    def _configure_session() -> requests.Session:
        """
        Configures and returns a requests.Session with automatic retries on certain status codes.

        This static method sets up the session object which the Interface will use for all HTTP
        communications. It adds automatic retries for the HTTP status codes in the `status_forcelist`,
        with a total of 5 retries and a backoff factor of 1.
        """
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[502, 503, 504],
        )
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def new_message(self) -> Message:
        """
        Creates and returns a new message object with a notification callback attached.

        This method should be called when the client needs to create a new message to be sent.
        It initializes a Message object and binds the `notify` method of the Interface as its
        notification callback function.
        """
        self.message = Message(notify=self.notify)
        return self.message

    def notify(self) -> None:
        """
        Notifies that a message is ready to be sent, triggering the send_message callback.

        If a message has been created using `new_message`, this method formats that message and
        uses the `send_message` callback to send it. It raises an exception if called before a message
        is created.
        """
        if self.message is None:
            raise Exception("Please create a message first")

        message_obj = self.message.to_dict()
        self.send_message(
            {
                "message_id": message_obj["id"],
                "interface": message_obj["interface"],
            }
        )

    def get_thread(self, nr: int = 5, to_string: bool = False) -> Any:
        """
        Retrieves and returns a thread of messages, with a limit on the number of messages.

        Args:
            nr: The number of messages to retrieve from the thread. Defaults to 5.
            to_string: A boolean flag indicating whether to convert the messages to a string. Defaults to False.

        The method delegates the operation to the `_run` callback, providing the required parameters.
        """
        return self._run(
            skill_id="s_get_thread", nr_of_messages=nr, to_string=to_string
        )

    def invoke(self, agent_id: str, **kwargs: Any) -> Any:
        """
        Invokes an agent or skill and returns its result.

        Args:
            agent_id: A string identifier of the agent or skill to be invoked.
            **kwargs: A variable number of keyword arguments that are passed to the agent or skill.

        This method utilizes the `_run` callback to execute the agent or skill identified by `agent_id`
        with the given keyword arguments.
        """
        return self._run(skill_id=agent_id, **kwargs)

    def _request(
        self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sends an HTTP request to the given endpoint with the provided payload and returns the response.

        Args:
            method: The HTTP method to use for the request.
            endpoint: The URL endpoint to which the request is sent.
            payload: A dictionary containing the payload for the request. Defaults to None.

        This method handles sending an HTTP request using the configured session object, including
        the API key for authorization. It also provides comprehensive error handling, raising more
        specific exceptions depending on the encountered HTTP error.
        """
        if payload is None:
            payload = {}
        payload["api_key"] = self.api_key
        try:
            response = self.session.request(method, endpoint, json=payload)
            # Raises HTTPError for bad responses
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if status in [401, 403]:
                raise AuthorizationError(
                    "Authorization error. Check your API key."
                ) from e
            elif status == 404:
                if endpoint in {READ_STATE_ENDPOINT, UPDATE_STATE_ENDPOINT}:
                    return self.create_state(self.user_id)
                else:
                    raise ResourceNotFoundError(f"Not found: {endpoint}") from e
            else:
                raise RequestError(f"Unexpected error: {e.response.content}") from e

    def create_state(
        self, state_id: str, state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Creates a new state entry for the given state_id with the provided state dictionary.

        Args:
            state_id: A string that uniquely identifies the state to create.
            state: An optional dictionary representing the state to be created. Defaults to an empty dict.

        This method creates a new state for the given `state_id` using the `_request` method.
        If a state is not provided, it initializes the state to an empty dictionary.
        """
        if state is None:
            state = {}
        result = self._request(
            "POST", CREATE_STATE_ENDPOINT, {"state_id": state_id, "state": state}
        )
        return result.get("data", {}).get("state", {})

    def read_state(self, state_id: str) -> Dict[str, Any]:
        """
        Reads and returns the state associated with the given state_id.

        Args:
            state_id: A string that uniquely identifies the state to read.

        This method retrieves the state data from the server for the provided `state_id` by using the `_request` method.
        """
        result = self._request("POST", READ_STATE_ENDPOINT, {"state_id": state_id})
        return result.get("data", {}).get("state", {})

    def update_state(self, state_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates the state associated with the given state_id with the provided state dictionary.

        Args:
            state_id: A string that uniquely identifies the state to update.
            state: A dictionary representing the new state data.

        This method sends an update request for the state corresponding to `state_id` with the new `state`.
        """
        result = self._request(
            "POST", UPDATE_STATE_ENDPOINT, {"state_id": state_id, "state": state}
        )
        return result.get("data", {}).get("state", {})

    @property
    def state(self):
        """
        Property that returns the state proxy associated with this interface.

        The state proxy provides a convenient way to manage the state data. It abstracts the details of
        state loading and saving through the provided StateProxy instance.
        """
        return self._state_proxy

    def load_state(self):
        """
        Loads the state data using the state proxy.

        This method is a convenient wrapper around the `load` method of the `_state_proxy` object,
        initiating the process of state data retrieval.
        """
        self._state_proxy.load()

    def save_state(self):
        """
        Saves the current state data using the state proxy.

        This method is a convenient wrapper around the `save` method of the `_state_proxy` object,
        initiating the process of state data saving. It ensures that the current state data is
        persisted through the associated interface.
        """
        self._state_proxy.save()
