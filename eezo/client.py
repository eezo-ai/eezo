from .errors import AuthorizationError, RequestError, ResourceNotFoundError
from typing import Optional, Callable, Dict, List, Any
from requests.packages.urllib3.util.retry import Retry
from watchdog.events import FileSystemEventHandler
from .interface.context import Context
from .interface.components import component_api_json_description
from requests.adapters import HTTPAdapter
from .interface.context import Message
from watchdog.observers import Observer
from .agent import Agents, Agent

import concurrent.futures
import socketio
import warnings
import requests
import logging
import sys
import time
import uuid
import traceback
import json
import os

from .state import StateProxy

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

CREATE_AGENT_ENDPOINT = SERVER + "/v1/create-agent/"
GET_AGENTS_ENDPOINT = SERVER + "/v1/get-agents/"
GET_AGENT_ENDPOINT = SERVER + "/v1/get-agent/"
DELETE_AGENT_ENDPOINT = SERVER + "/v1/delete-agent/"
UPDATE_AGENT_ENDPOINT = SERVER + "/v1/update-agent/"

GET_TREAD_ENDPOINT = SERVER + "/v1/get-thread/"


class RestartHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            os.execl(sys.executable, sys.executable, *sys.argv)


class JobCompleted:
    def __init__(
        self,
        job_id: str,
        result: Dict,
        success: bool,
        error=None,
        traceback=None,
        error_tag=None,
    ):
        self.result = result
        self.job_id = job_id
        self.success = success
        self.error = error
        self.traceback = traceback
        self.error_tag = error_tag

    def to_dict(self):
        return {
            "result": self.result,
            "job_id": self.job_id,
            "success": self.success,
            "error": self.error,
            "traceback": self.traceback,
            "error_tag": self.error_tag,
        }


class EnvironmentVariable:
    key: str
    value: str


class Client:
    def __init__(self, api_key: Optional[str] = None, logger: bool = False) -> None:
        """Initialize the Client with an optional API key and a logger flag.

        Args:
            api_key (Optional[str]): The API key for authentication. If None, it defaults to the EEZO_API_KEY environment variable.
            logger (bool): Flag to enable logging.

        Raises:
            ValueError: If api_key is None after checking the environment.
        """
        self.api_key: str = (
            api_key if api_key is not None else os.getenv("EEZO_API_KEY")
        )
        if not self.api_key:
            raise ValueError("Eezo api_key is required")

        self.agent_registry: Dict[str, Callable] = {}
        self.futures: List[concurrent.futures.Future] = []
        self.executor: concurrent.futures.ThreadPoolExecutor = (
            concurrent.futures.ThreadPoolExecutor()
        )
        self.observer = Observer()

        self.logger: bool = logger
        if self.logger:
            logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

        self.state_was_loaded = False
        self.user_id: Optional[str] = os.environ.get("EEZO_USER_ID", None)
        self.auth_token: Optional[str] = os.environ.get("EEZO_TOKEN", None)
        self.job_responses: Dict[str, str] = {}
        self.run_loop = True
        self.sio: Optional[socketio.Client] = None
        self.emit_buffer: List[Dict] = []

        self.session = self._configure_session()

        if not self.user_id or not self.auth_token:
            result = self._request("POST", AUTH_URL, {"api_key": self.api_key})
            self.user_id = result.get("user_id")
            self.auth_token = result.get("token")
            os.environ["EEZO_USER_ID"] = self.user_id
            os.environ["EEZO_TOKEN"] = self.auth_token
        else:
            logging.info("Already authenticated")

        self._state_proxy: StateProxy = StateProxy(self)

    @staticmethod
    def component_api_description() -> str:
        """
        Returns the UI component API as a string.
        """
        return component_api_json_description

    @staticmethod
    def _configure_session() -> requests.Session:
        """
        Configures and returns a requests.Session with automatic retries on certain status codes.

        This static method sets up the session object which the Context will use for all HTTP
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

    def create_agent(
        self,
        agent_id: str,
        description: str,
        input_schema: Optional[dict] = {},
        output_schema: Optional[dict] = {},
        environment_variables: Optional[List[EnvironmentVariable]] = [],
    ) -> Agent:
        """Create a new agent with the given agent_id

        Args:
            agent_id (str): The ID for the new agent.
            description (str): Describes when to activate the agent.
            input_schema (Optional[dict]): Needs to be a valid JSON schema.
            output_schema (Optional[dict]): Needs to be a valid JSON schema.
            environment_variables (Optional[List[EnvironmentVariable]]): A list of key-value pairs like:
                [{"key": "key", "value": "value"}]

        Returns:
            Agent: The newly created agent object.
        """
        Agent.validate_json_schema(input_schema)
        Agent.validate_json_schema(output_schema)
        Agent.validate_environment_variables(environment_variables)

        response = self._request(
            "POST",
            CREATE_AGENT_ENDPOINT,
            {
                "api_key": self.api_key,
                "agent_id": agent_id,
                "description": description,
                "input_schema": input_schema,
                "output_schema": output_schema,
                "environment_variables": environment_variables,
            },
        )
        if response.get("error"):
            raise Exception(response.get("error"))
        agent_dict = response["data"]
        return Agent(**agent_dict)

    def update_agent(
        self,
        agent_id: str,
        description: Optional[str] = "",
        input_schema: Optional[dict] = {},
        output_schema: Optional[dict] = {},
        environment_variables: Optional[List[EnvironmentVariable]] = [],
    ) -> Agent:
        """Update an existing agent with the given ID.

        Args:
            agent_id (str): The ID of the agent to update.
            description (Optional[str]): Describes when to activate the agent.
            input_schema (Optional[dict]): Needs to be a valid JSON schema.
            output_schema (Optional[dict]): Needs to be a valid JSON schema.
            environment_variables (Optional[List[EnvironmentVariable]]): A list of key-value pairs like:
                [{"key": "key", "value": "value"}]

        Returns:
            Agent: The updated agent object.
        """
        Agent.validate_json_schema(input_schema)
        Agent.validate_json_schema(output_schema)
        Agent.validate_environment_variables(environment_variables)

        response = self._request(
            "POST",
            UPDATE_AGENT_ENDPOINT,
            {
                "api_key": self.api_key,
                "agent_id": agent_id,
                "description": description,
                "input_schema": input_schema,
                "output_schema": output_schema,
                "environment_variables": environment_variables,
            },
        )
        if response.get("error"):
            raise Exception(response.get("error"))
        agent_dict = response["data"]
        return Agent(**agent_dict)

    def delete_agent(self, agent_id: str) -> None:
        """Delete an agent by its ID.

        Args:
            agent_id (str): The ID of the agent to delete.
        """
        self._request(
            "POST",
            DELETE_AGENT_ENDPOINT,
            {
                "api_key": self.api_key,
                "agent_id": agent_id,
            },
        )

    def on(self, agent_id: str) -> Callable:
        """Decorator to register an agent

        Args:
            agent_id (str): The identifier for the agent.

        Returns:
            Callable: The decorator function.
        """

        def decorator(func: Callable) -> Callable:
            if not callable(func):
                raise TypeError(f"Expected a callable, got {type(func)} instead")
            self.register_agent(agent_id, func)
            return func

        return decorator

    def add_connector(self, agent_id: str, func: Callable) -> None:
        """Add an agent function to the client.

        Args:
            agent_id (str): The identifier for the agent.
            func (Callable): The agent to add.
        """
        warnings.warn(
            "The 'add_connector' function is deprecated and will be removed in a future version. "
            "Please use 'register_agent' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.agent_registry[agent_id] = func

    def register_agent(self, agent_id: str, func: Callable) -> None:
        """Register agent.

        Args:
            agent_id (str): The identifier for the agent.
            func (Callable): The agent to add.
        """
        self.agent_registry[agent_id] = func

    def _run(
        self,
        agent_id: str,
        current_job_id: str,
        wait_for_response: bool = True,
        **kwargs,
    ):
        """Invoke a skill and get the result."""
        if not agent_id:
            raise ValueError("agent_id is required")

        job_id = str(uuid.uuid4())
        self.sio.emit(
            "invoke_skill",
            {
                "new_job_id": job_id,
                "agent_id": agent_id,
                "skill_payload": kwargs,
                "job_id": current_job_id,
            },
        )

        while True and wait_for_response:
            if job_id in self.job_responses:
                response = self.job_responses.pop(job_id)

                if not response.get("success", True):
                    logging.info(
                        f"<< Sub Job {response['id']} failed:\n{response['traceback']}."
                    )
                    raise Exception(response["error"])

                logging.info(f"<< Sub Job {job_id} \033[32mcompleted\033[0m.")
                return response["result"]
            else:
                time.sleep(1)

    def _emit_safe(self, event: str, agent_id: str, data: Dict) -> None:
        if self.sio.connected:
            self.sio.emit(event, data)
        else:
            logging.info(
                f"Connection down. Buffering job result for '{event}' for agent {agent_id}."
            )
            self.emit_buffer.append(
                {
                    "data": data,
                    "event": event,
                    "agent_id": agent_id,
                    "job_id": data["job_id"],
                }
            )

    def _execute_job(self, job_obj):
        (
            job_id,
            agent_uid,
            agent_id,
            eezo_id,
            thread_id,
            payload,
            environment_variables,
        ) = (
            job_obj["job_id"],
            job_obj["agent_uid"],
            job_obj["agent_id"],
            job_obj["eezo_id"],
            job_obj["thread_id"],
            job_obj["job_payload"],
            job_obj["environment_variables"],
        )
        logging.info(
            f"<< Job {job_id} received for agent {agent_id} - payload: {payload} - env_vars: {environment_variables}"
        )

        c: Context = Context(
            job_id=job_id,
            user_id=self.user_id,
            api_key=self.api_key,
            agent_id=agent_id,
            eezo_id=eezo_id,
            thread_id=thread_id,
            environment_variables=environment_variables,
            cb_rest_api=self._request,
            cb_run=self._run,
        )

        def execute():
            try:
                self._emit_safe("confirm_job_request", agent_id, {"job_id": job_id})

                try:
                    result = self.agent_registry[agent_id](c, **payload)
                except Exception as e:
                    logging.info(
                        f" ✖ Agent {agent_id} failed processing job {job_id}:\n{traceback.format_exc()}"
                    )
                    job_completed = JobCompleted(
                        job_id=job_id,
                        result=None,
                        success=False,
                        error=str(e),
                        traceback=str(traceback.format_exc()),
                        error_tag="Agent Error",
                    ).to_dict()
                    self._emit_safe("job_completed", agent_id, job_completed)

                    return

                job_completed = JobCompleted(job_id, result, True).to_dict()

                self._emit_safe("job_completed", agent_id, job_completed)
            except Exception as e:
                logging.info(
                    f" ✖ Client error while agent {agent_id} was processing job {job_id}:\n{traceback.format_exc()}"
                )
                job_completed = JobCompleted(
                    job_id=job_id,
                    result=None,
                    success=False,
                    error=str(e),
                    traceback=str(traceback.format_exc()),
                    error_tag="Client Error",
                ).to_dict()
                self._emit_safe("job_completed", agent_id, job_completed)

        self.executor.submit(execute)

    def connect(self) -> None:
        """Connect to the Eezo server and start the client. This involves scheduling
        tasks in a thread pool executor and handling responses."""
        try:
            self.observer.schedule(RestartHandler(), ".", recursive=False)
            self.observer.start()

            self.sio = socketio.Client(
                reconnection_attempts=0,
                reconnection_delay_max=10,
                reconnection_delay=1,
                engineio_logger=False,
                logger=False,
            )

            @self.sio.event
            def connect():
                agent_ids = list(set(self.agent_registry.keys()))
                self.sio.emit(
                    "authenticate",
                    {
                        "token": self.auth_token,
                        "agent_ids": agent_ids,
                        "key": self.api_key,
                    },
                )

            if not self.auth_token:
                raise Exception("Not authenticated")

            def auth_error(message: str):
                logging.info(f" ✖ Authentication failed: {message}")
                self.run_loop = False
                self.sio.disconnect()

            # Both functions have to address the right agent
            self.sio.on("job_request", lambda p: self._execute_job(p))

            self.sio.on(
                "job_response", lambda p: self.job_responses.update({p["id"]: p})
            )

            self.sio.on("token_expired", lambda: self.authenticate())
            self.sio.on("auth_error", auth_error)

            def send_buffered_jobs(payload):
                logging.info(f" ✔ Agent {payload['agent_id']} \033[32mconnected\033[0m")

                # Check for buffered messages for this agent
                removed_items = []
                for item in self.emit_buffer:
                    if item["agent_id"] == payload["agent_id"]:
                        logging.info(
                            f">> Sending buffered message for job {item['job_id']} to '{item['event']}'"
                        )
                        self.sio.emit(item["event"], item["data"])
                        removed_items.append(item)

                for item in removed_items:
                    self.emit_buffer.remove(item)

            # When the server notifies that an agent is online, send buffered jobs
            self.sio.on("agent_online", send_buffered_jobs)

            def disconnect():
                for agent_id in self.agent_registry:
                    logging.info(f" ✖ Agent {agent_id} \033[31mdisconnected\033[0m")

            self.sio.on("disconnect", lambda: disconnect())

            while self.run_loop:
                try:
                    self.sio.connect(SERVER)
                    self.sio.wait()
                except socketio.exceptions.ConnectionError as e:
                    if self.run_loop:
                        if self.logger:
                            logging.info(
                                f" ✖ Failed to connect to Eezo server with error: {e}"
                            )
                            logging.info("   Retrying to connect...")
                        time.sleep(5)
                    else:
                        break
                except KeyboardInterrupt:
                    self.run_loop = False
                    break
                except Exception as e:
                    if self.run_loop:
                        if self.logger:
                            logging.info(
                                f" ✖ Failed to connect to Eezo server with error: {e}"
                            )
                            logging.info("   Retrying to connect...")
                        time.sleep(5)
                    else:
                        break

                self.sio.disconnect()

        except KeyboardInterrupt:
            pass
        finally:
            self.observer.stop()

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
            response = self.session.request(method, endpoint, json=payload, timeout=10)
            # Raises HTTPError for bad responses
            response.raise_for_status()
            logging.info(f"Request to {endpoint} successful \033[32m200\033[0m")
            return response.json()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code

            # Parse error message
            error_message = e.response.text
            if "detail" in error_message:
                error_message = json.loads(error_message)["detail"]

            if status in [401, 403]:
                logging.error(
                    "Eezo \033[31mauthorization error\033[0m. Check your API key."
                )
                raise AuthorizationError(
                    "Authorization error. Check your API key."
                ) from e
            elif status == 404:
                if endpoint in {READ_STATE_ENDPOINT, UPDATE_STATE_ENDPOINT}:
                    return self.create_state(self.user_id)
                else:
                    logging.error(f"Resource not found: \033[31m{error_message}\033[0m")
                    raise ResourceNotFoundError(error_message) from e
            else:
                logging.error(f"Error: \033[31m{error_message}\033[0m")
                raise RequestError(f"Error: {error_message}") from e

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
            self._request(
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
        self._request(
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
        response = self._request(
            "POST",
            READ_MESSAGE_ENDPOINT,
            {
                "api_key": self.api_key,
                "message_id": message_id,
            },
        )

        if "data" not in response:
            raise Exception(f"Message not found for id {message_id}")
        old_message_obj = response["data"]

        new_message = None

        def notify():
            messgage_obj = new_message.to_dict()
            self._request(
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
        response = self._request("POST", GET_AGENTS_ENDPOINT, {"api_key": self.api_key})
        agents_dict = response["data"]
        agents = Agents(agents_dict)
        if online_only:
            agents.agents = [agent for agent in agents.agents if agent.is_online()]

        return agents

    def get_agent(self, agent_id: str) -> Agent | None:
        """Retrieve and return an agent by its ID.

        Args:
            agent_id (str): The ID of the agent to retrieve.

        Returns:
            Agent: The agent object or None if not found.

        Raises:
            Exception: If the agent with the given ID is not found.
        """
        response = self._request(
            "POST", GET_AGENT_ENDPOINT, {"api_key": self.api_key, "agent_id": agent_id}
        )
        agent_dict = response["data"]
        if agent_dict:
            return Agent(**agent_dict)
        else:
            return None

    def get_thread(
        self, eezo_id: str, thread_id: str, nr: int = 5, to_string: bool = False
    ) -> Any:
        """Retrieve and return a thread of messages, with a limit on the number of messages.

        Args:
            eezo_id (str): The Eezo user identifier.
            thread_id (str): The thread identifier.
            nr (int): The number of messages to retrieve from the thread. Defaults to 5.
            to_string (bool): Flag to convert the messages to a string. Defaults to False.

        Returns:
            Any: The thread of messages.
        """
        return self._request(
            "POST",
            GET_TREAD_ENDPOINT,
            {
                "api_key": self.api_key,
                "thread_id": thread_id,
                "eezo_id": eezo_id,
                "to_string": to_string,
                "number_of_messages": nr,
            },
        )

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
        Property that returns the state proxy associated with this client.

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
        persisted through the associated client.
        """
        self._state_proxy.save()
