from typing import Any, Dict, Callable, Optional
from .message import Message

import os

SERVER = "https://api-service-bofkvbi4va-ey.a.run.app"
if os.environ.get("EEZO_DEV_MODE") == "True":
    print("Running in dev mode")
    SERVER = "http://localhost:8082"

CREATE_MESSAGE_ENDPOINT = SERVER + "/v1/create-message/"

GET_TREAD_ENDPOINT = SERVER + "/v1/get-thread/"


class Context:
    """
    The Context class provides access to the job-specific state and messaging systems.

    Attributes:
        job_id: Identifier for the specific job this interface is associated with.
        user_id: User identifier for state and message association.
        api_key: API key for authorization purposes.
        environment_variables: Dictionary of environment variables for the job.
        send_message: Callback function to send messages.
        _run: Private callback function to execute skills or agents.
    """

    def __init__(
        self,
        job_id: str,
        user_id: str,
        api_key: str,
        agent_id: str,
        eezo_id: str,
        thread_id: str,
        environment_variables: Dict[str, Any],
        cb_run: Callable[..., Any],
        cb_rest_api: Callable[..., Any],
    ):
        """
        Initialize the Context with identifiers and callback functions.

        Args:
            job_id: A unique identifier for the job to which this interface pertains.
            user_id: A unique identifier for the user who is associated with this job.
            api_key: A string that represents the API key for authentication.
            agent_id: A string that represents the agent ID.
            eezo_id: A string that represents the eezo ID.
            thread_id: A string that represents the thread ID.
            environment_variables: A dictionary of environment variables for the job.
            cb_run: A callback function that is used to execute agents or skills.

        The Context class acts as a facilitator between the client's job-specific operations and the server's
        state management and messaging systems. It encapsulates methods for message creation, notification,
        state retrieval, and invocation of external skills or agents.
        """
        self.job_id = job_id
        self.message: Optional[Message] = None
        self.user_id = user_id
        self.api_key = api_key
        self.agent_id = agent_id
        self.eezo_id = eezo_id
        self.thread_id = thread_id
        self.environment_variables = environment_variables
        self._run = cb_run
        self._request = cb_rest_api

    def new_message(self) -> Message:
        """
        Creates and returns a new message object with a notification callback attached.

        This method should be called when the client needs to create a new message to be sent.
        It initializes a Message object and binds the `notify` method of the Context as its
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
        self._request(
            "POST",
            CREATE_MESSAGE_ENDPOINT,
            {
                "api_key": self.api_key,
                "thread_id": self.thread_id,
                "eezo_id": self.eezo_id,
                "message_id": message_obj["id"],
                "interface": message_obj["interface"],
                "context": self.agent_id,
            },
        )

    def get_thread(self, nr: int = 5, to_string: bool = False) -> Any:
        """
        Retrieves and returns a thread of messages, with a limit on the number of messages.

        Args:
            nr: The number of messages to retrieve from the thread. Defaults to 5.
            to_string: A boolean flag indicating whether to convert the messages to a string. Defaults to False.

        The method delegates the operation to the `_run` callback, providing the required parameters.
        """
        return self._request(
            "POST",
            GET_TREAD_ENDPOINT,
            {
                "api_key": self.api_key,
                "thread_id": self.thread_id,
                "eezo_id": self.eezo_id,
                "to_string": to_string,
                "number_of_messages": nr,
            },
        )

    def invoke(self, agent_id: str, **kwargs: Any) -> Any:
        """
        Invokes an agent and returns its result.

        Args:
            agent_id: A string identifier of the agent to be invoked.
            **kwargs: A variable number of keyword arguments that are passed to the agent.

        This method utilizes the `_run` callback to execute the agent identified by `agent_id`
        with the given keyword arguments.
        """
        return self._run(
            agent_id=agent_id,
            current_job_id=self.job_id,
            wait_for_response=True,
            **kwargs
        )

    def invoke_async(self, agent_id: str, **kwargs: Any) -> None:
        """
        Triggers an agent without waiting for a response.

        Args:
            agent_id: A string identifier of the agent to be triggered.
            **kwargs: A variable number of keyword arguments that are passed to the agent.

        This method uses the `_run` callback to trigger the agent identified by `agent_id`
        with the given keyword arguments.
        """
        self._run(
            agent_id=agent_id,
            current_job_id=self.job_id,
            wait_for_response=False,
            **kwargs
        )
