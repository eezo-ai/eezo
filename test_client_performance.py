from concurrent.futures import ThreadPoolExecutor

import asyncio
import dotenv
import time
import os

dotenv.load_dotenv()

from eezo import Eezo
from eezo import AsyncEezo


# Direct message test ---------------------------------------------------------


def send_messages(i: int):
    e = Eezo(logger=True)
    # Send a message to the Chat UI
    m = e.new_message(
        eezo_id=os.environ["DEMO_EEZO_ID"],
        thread_id=os.environ["DEMO_THREAD_ID"],
        context="test " + str(i),
    )

    m.add("text", text="Hello, world " + str(i) + "!")
    m.notify()

    time.sleep(3)

    # Update the message in Chat UI
    m = e.update_message(m.id)
    m.add("text", text="Hello, world! Updated " + str(i) + "!")
    m.notify()

    time.sleep(3)

    # Delete the message from Chat UI
    e.delete_message(m.id)


# WS test ---------------------------------------------------------------------


async def connect_client():
    e = AsyncEezo(logger=True)

    @e.on(os.environ["DEMO_AGENT_ID"])
    async def chart_demo(server, **kwargs):
        m = server.new_message()
        m.add(
            "chart",
            chart_type="candlestick",
            data=[[10, 15, 5, 12], [11, 13, 9, 8], [12, 12, 10, 11]],
            xaxis=["a", "b", "c"],
            name="Example chart",
            chart_title="Example chart",
        )
        await m.notify()

    await e.connect()


async def stress_test(num_connections):
    tasks = [connect_client() for _ in range(num_connections)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    # with ThreadPoolExecutor(max_workers=10) as executor:
    #     # Submit tasks to be executed
    #     for i in range(10):
    #         executor.submit(send_messages, i)

    asyncio.run(stress_test(100))
