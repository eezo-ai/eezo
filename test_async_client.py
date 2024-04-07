import asyncio
import dotenv
import json
import time
import os

dotenv.load_dotenv()

from eezo import AsyncEezo


e = AsyncEezo(logger=True)


async def sent_directly():
    m = await e.new_message(
        eezo_id=os.environ["DEMO_EEZO_ID"],
        thread_id=os.environ["DEMO_THREAD_ID"],
        context="test",
    )

    m.add("text", text="Hello, world!")
    await m.notify()

    time.sleep(3)

    m = await e.update_message(m.id)
    m.add("text", text="Hello, world! Updated!")
    await m.notify()

    time.sleep(3)

    await e.delete_message(m.id)


asyncio.run(sent_directly())


@e.on(os.environ["DEMO_AGENT_ID_1"])
async def chart_demo(c, **kwargs):
    m = c.new_message()
    m.add("text", text="Hello, world 1")
    m.add(
        "chart",
        chart_type="candlestick",
        data=[[10, 15, 5, 12], [11, 13, 9, 8], [12, 12, 10, 11]],
        xaxis=["a", "b", "c"],
        name="Example chart",
        chart_title="Example chart",
    )
    await m.notify()


@e.on(os.environ["DEMO_AGENT_ID_2"])
async def chart_demo(c, **kwargs):
    m = c.new_message()
    m.add("text", text="Hello, world 2")
    thread_str = await c.get_thread(to_string=True)
    m.add("text", text=f"```{thread_str}```")
    await m.notify()


asyncio.run(e.connect())
