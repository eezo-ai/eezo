from .message import Message

import uuid


class AsyncInterface:
    def __init__(
        self,
        job_id: str,
        cb_send_message: callable,
        cb_invoke_connector: callable,
        cb_get_result: callable,
    ):
        self.job_id = job_id
        self.message = None
        self.send_message: callable = cb_send_message
        self.invoke_connector: callable = cb_invoke_connector
        self.get_result: callable = cb_get_result

    def new_message(self):
        self.message = Message(self.notify)
        return self.message

    async def notify(self):
        if self.message is None:
            raise Exception("Please create a message first")
        message_obj = self.message.to_dict()
        await self.send_message(
            {
                "message_id": message_obj["id"],
                "interface": message_obj["interface"],
            }
        )

    async def _run(self, skill_id, **kwargs):
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

    async def get_thread(self, nr=5, to_string=False):
        return await self._run(
            skill_id="s_get_thread", nr_of_messages=nr, to_string=to_string
        )

    async def invoke(self, agent_id, **kwargs):
        return await self._run(skill_id=agent_id, **kwargs)


class Interface:
    def __init__(
        self,
        job_id: str,
        cb_send_message: callable,
        cb_invoke_connector: callable,
        cb_get_result: callable,
    ):
        self.job_id = job_id
        self.message = None
        self.send_message = cb_send_message
        self.invoke_connector = cb_invoke_connector
        self.get_result = cb_get_result

    def new_message(self):
        self.message = Message(notify=self.notify)
        return self.message

    def notify(self):
        if self.message is None:
            raise Exception("Please create a message first")

        message_obj = self.message.to_dict()
        self.send_message(
            {
                "message_id": message_obj["id"],
                "interface": message_obj["interface"],
            }
        )

    def _run(self, skill_id, **kwargs):
        """Invoke a skill and get the result."""
        if not skill_id:
            raise ValueError("skill_id is required")

        job_id = str(uuid.uuid4())
        self.invoke_connector(
            {
                "new_job_id": job_id,
                "skill_id": skill_id,
                "skill_payload": kwargs,
            }
        )
        return self.get_result(job_id)

    def get_thread(self, nr=5, to_string=False):
        return self._run(
            skill_id="s_get_thread", nr_of_messages=nr, to_string=to_string
        )

    def invoke(self, agent_id, **kwargs):
        return self._run(skill_id=agent_id, **kwargs)
