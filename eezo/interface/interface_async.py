from typing import Any, Dict, Callable, Optional
from .message import Message

import uuid


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
