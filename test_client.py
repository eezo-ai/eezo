import concurrent.futures
import dotenv
import time
import os

dotenv.load_dotenv()

from eezo import Eezo


e = Eezo(logger=True)

# m = e.new_message(
#     eezo_id=os.environ["DEMO_EEZO_ID"],
#     thread_id=os.environ["DEMO_THREAD_ID"],
#     context="test",
# )

# m.add("text", text="Hello, world!")
# m.notify()

# time.sleep(3)

# m = e.update_message(m.id)
# m.add("text", text="Hello, world! Updated!")
# m.notify()

# time.sleep(3)

# e.delete_message(m.id)


def invoke(c, num_executions):
    def invoke_query(i):
        return c.invoke(
            os.environ["DEMO_AGENT_ID_1"], query=f"AI no code platforms {i}"
        )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(invoke_query, i) for i in range(num_executions)]
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]
        return results


@e.on(os.environ["DEMO_AGENT_ID_1"])
def chart_demo(c, **kwargs):
    m = c.new_message()
    m.add("text", text=f"Hello, world 1. Query: {kwargs.get('query')}")
    m.add(
        "chart",
        chart_type="candlestick",
        data=[[10, 15, 5, 12], [11, 13, 9, 8], [12, 12, 10, 11]],
        xaxis=["a", "b", "c"],
        name="Example chart",
        chart_title="Example chart",
    )
    m.notify()
    return {"status": "success"}


@e.on(os.environ["DEMO_AGENT_ID_2"])
def chart_demo(c, **kwargs):
    m = c.new_message()
    m.add("text", text="Hello, world 2")
    # thread_str = c.get_thread(to_string=True)
    # m.add("text", text=f"```{thread_str}```")
    m.notify()

    results = invoke(c, 3)
    m.add("text", text=f"Result from Agent 1: {results}")
    m.notify()

    # agents = c.get_agents()
    # m.add("text", text=f"Agents: {agents}")
    # m.notify()

    # c.load_state()

    # print(c.state)
    # print(c.state["test"])
    # print(c.state.get("test"))

    # c.state["test"] = c.state.get("test", 0) + 1
    # m.add("text", text=f"State: {c.state['test']}")
    # m.notify()

    # c.save_state()


e.connect()
