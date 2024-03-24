import asyncio
import dotenv
import time
import os

dotenv.load_dotenv()

from eezo import AsyncEezo


e = AsyncEezo(logger=True)


async def sent_directly():
    # Send a message to Chat UI
    m = await e.new_message(
        eezo_id=os.environ["DEMO_EEZO_ID"],
        thread_id=os.environ["DEMO_THREAD_ID"],
        context="test",
    )

    m.add("text", text="Hello, world!")
    await m.notify()

    time.sleep(3)

    # Update the message in Chat UI
    m = await e.update_message(m.id)
    m.add("text", text="Hello, world! Updated!")
    await m.notify()

    time.sleep(3)

    # Delete the message from Chat UI
    await e.delete_message(m.id)


asyncio.run(sent_directly())


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

    # result = server.get_thread()

    # formatted_json = json.dumps(result, indent=4)
    # m.add("text", text=f"```{formatted_json}```")
    # await m.notify()


asyncio.run(e.connect())
