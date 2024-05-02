from typing import Any, Dict, Callable, Optional
from .message import Message


class Interface:
    """
    Interface class for managing communications and state for a specific job identified by a job ID.

    Attributes:
        job_id: Identifier for the specific job this interface is associated with.
        user_id: User identifier for state and message association.
        api_key: API key for authorization purposes.
        send_message: Callback function to send messages.
        _run: Private callback function to execute skills or agents.
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
                "job_id": self.job_id,
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
            skill_id="s_get_thread",
            current_job_id=self.job_id,
            nr_of_messages=nr,
            to_string=to_string,
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
        return self._run(skill_id=agent_id, current_job_id=self.job_id, **kwargs)
