from eezo import AsyncEezo

import asyncio
import dotenv
import os

dotenv.load_dotenv()

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

    # result = server.get_thread()

    # formatted_json = json.dumps(result, indent=4)
    # m.add("text", text=f"```{formatted_json}```")
    # await m.notify()


asyncio.run(e.connect())
