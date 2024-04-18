import asyncio
import dotenv
import json
import time
import os

dotenv.load_dotenv()

from eezo import AsyncEezo


e = AsyncEezo(logger=True)


async def sent_directly():
    await e.load_state()

    print(e.state)
    print(e.state["test"])
    print(e.state.get("test"))

    e.state["test"] = e.state.get("test", 0) + 1
    m = await e.new_message(
        eezo_id=os.environ["DEMO_EEZO_ID"],
        thread_id=os.environ["DEMO_THREAD_ID"],
        context="test",
    )
    m.add("text", text=f"State: {e.state['test']}")
    await m.notify()

    await e.save_state()

    agents = await e.get_agents()
    for agent in agents.agents:
        print("--------------------------------------------------")
        print(agent.id)
        print(agent.name)
        print(agent.description)
        print(agent.status)
        print(agent.properties_schema)
        print(agent.properties_required)
        print(agent.return_schema)
        print(agent.input_model)
        print(agent.output_model)
        print()
        print(agent.is_online())
        print(agent.to_dict())
        print("--------------------------------------------------")

    agent = await e.get_agent("632f7b38-5982-4e6e-ab99-6468d37e4a64")
    print("--------------------------------------------------")
    print(agent.id)
    print(agent.name)
    print(agent.description)
    print(agent.status)
    print(agent.properties_schema)
    print(agent.properties_required)
    print(agent.return_schema)
    print(agent.input_model)
    print(agent.output_model)
    print()
    print(agent.is_online())
    print(agent.to_dict())
    print(agent.llm_string())
    print("--------------------------------------------------")

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
    return {"status": "success", "test": "test"}


@e.on(os.environ["DEMO_AGENT_ID_2"])
async def chart_demo(c, **kwargs):
    m = c.new_message()
    m.add("text", text="Hello, world 2")
    thread_str = await c.get_thread(to_string=True)
    m.add("text", text=f"```{thread_str}```")
    thread_str = await c.get_thread()
    m.add("text", text=f"```{thread_str}```")
    await m.notify()

    result = await c.invoke(os.environ["DEMO_AGENT_ID_1"], query="AI no code platforms")
    m.add("text", text=f"Result: {result}")
    await m.notify()

    await c.load_state()

    print(c.state)
    print(c.state["test"])
    print(c.state.get("test"))

    c.state["test"] = c.state.get("test", 0) + 1
    m.add("text", text=f"State: {c.state['test']}")
    await m.notify()

    await c.save_state()


asyncio.run(e.connect())
