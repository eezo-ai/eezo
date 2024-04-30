import concurrent.futures
import dotenv
import os

dotenv.load_dotenv()
print("EEZO_DEV_MODE:", os.environ["EEZO_DEV_MODE"] == "True")

from eezo import Eezo


e = Eezo(logger=True)

# time.sleep(1)

# e = Eezo(logger=True)


# e.load_state()

# print(e.state)
# print(e.state["test"])
# print(e.state.get("test"))

# e.state["test"] = e.state.get("test", 0) + 1
# m = e.new_message(
#     eezo_id=os.environ["DEMO_EEZO_ID"],
#     thread_id=os.environ["DEMO_THREAD_ID"],
#     context="test",
# )
# m.add("text", text=f"State: {e.state['test']}")
# m.notify()

# e.save_state()

# agents = e.get_agents()
# for agent in agents.agents:
#     print("--------------------------------------------------")
#     print(agent.id)
#     print(agent.name)
#     print(agent.description)
#     print(agent.status)
#     print(agent.properties_schema)
#     print(agent.properties_required)
#     print(agent.return_schema)
#     print(agent.input_model)
#     print(agent.output_model)
#     print()
#     print(agent.is_online())
#     print(agent.to_dict())
#     print("--------------------------------------------------")

# agent = e.get_agent("632f7b38-5982-4e6e-ab99-6468d37e4a64")
# print("--------------------------------------------------")
# print(agent.id)
# print(agent.name)
# print(agent.description)
# print(agent.status)
# print(agent.properties_schema)
# print(agent.properties_required)
# print(agent.return_schema)
# print(agent.input_model)
# print(agent.output_model)
# print()
# print(agent.is_online())
# print(agent.to_dict())
# print(agent.llm_string())
# print("--------------------------------------------------")

m = e.new_message(
    eezo_id=os.environ["DEMO_EEZO_ID"],
    thread_id="asd",
    context="test",
)

m.add("text", text="Hello, world!")
m.notify()

exit()

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
    print("Chart demo")
    m = c.new_message()
    m.add("text", text=f"Hello, world 1. Query: {kwargs.get('query')}")
    # m.add(
    #     "chart",
    #     chart_type="candlestick",
    #     data=[[10, 15, 5, 12], [11, 13, 9, 8], [12, 12, 10, 11]],
    #     xaxis=["a", "b", "c"],
    #     name="Example chart",
    #     chart_title="Example chart",
    # )
    m.notify()
    return {"status": "success", "test": "test"}


@e.on(os.environ["DEMO_AGENT_ID_2"])
def invoke_demo(c, **kwargs):
    print("Invoke demo")
    m = c.new_message()
    m.add("text", text="Hello, world 2")
    # thread_str = c.get_thread(to_string=True)
    # m.add("text", text=f"```{thread_str}```")
    # thread_str = c.get_thread()
    # m.add("text", text=f"```{thread_str}```")
    m.notify()

    results = invoke(c, 3)
    m.add("text", text=f"Result from Agent 1: {results}")
    m.notify()


e.connect()
