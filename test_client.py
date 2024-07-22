import concurrent.futures
import dotenv
import time
import os

dotenv.load_dotenv()

from eezo import Eezo
from eezo.interface import Context

e = Eezo(logger=True)

agent = e.get_agent("this-agent-does-not-exist")
print(agent)

try:
    e.create_agent(
        agent_id="demo-1",
        description="Invoke when user says demo 1 or demo agent 1",
        environment_variables=[{"key": 123, "value": "new_key"}],
        output_schema={
            "status": {
                "type": "string",
                "description": "Status of the agent",
            },
            "test": {
                "type": "string",
                "description": "Test field",
            },
        },
    )
except Exception as error:
    print(error)

try:
    e.create_agent(
        agent_id="demo-3",
        description="Invoke when user says demo 2 or demo agent 2",
        environment_variables=[{"key": "test", "value": "deed"}],
    )
except Exception as error:
    print(error)

e.delete_agent("demo-3")

e.create_agent(
    agent_id="demo-3",
    description="Invoke when user says demo 2 or demo agent 2",
    environment_variables=[{"key": "test", "value": "deed"}],
)

# Test invalid json schema
try:
    e.create_agent(
        agent_id="demo_agent_3",
        description="Invoke when user says demo 3 or demo agent 3",
        input_schema="invalid",
        output_schema={},
    )
except ValueError as error:
    print(error)


time.sleep(1)

e = Eezo(logger=True)


e.load_state()

print(e.state)
try:
    print(e.state["test"])
except KeyError as error:
    e.state["test"] = 0

print(e.state.get("test"))

try:
    print(e.state["asd"])
except KeyError as error:
    print("State error test", error)

e.state["test"] = e.state.get("test", 0) + 1

m = e.new_message(
    eezo_id=os.environ["DEMO_EEZO_ID"],
    thread_id=os.environ["DEMO_THREAD_ID"],
    context="test",
)
m.add("text", text=f"State: {e.state['test']}")
m.notify()

e.save_state()

result = e.get_agents()
for agent in result.agents:
    print("--------------------------------------------------")
    print(agent.agent_id)
    print(agent.description)
    print(agent.status)
    print(agent.properties_required)
    print(agent.input_schema)
    print(agent.input_model)
    print(agent.output_schema)
    print(agent.output_model)
    try:
        print(agent.environment_variables)
    except Exception as e:
        print("No environment variables")
    print()
    print(agent.is_online())
    print(agent.to_dict())
    print("--------------------------------------------------")

agent = e.get_agent("demo-1")
print("--------------------------------------------------")
print(agent.agent_id)
print(agent.description)
print(agent.status)
print(agent.properties_required)
print(agent.input_schema)
print(agent.input_model)
print(agent.output_schema)
print(agent.output_model)
try:
    print(agent.environment_variables)
except Exception as e:
    print("No environment variables")
print()
print(agent.is_online())
print(agent.to_dict())
print(agent.llm_string())
print("--------------------------------------------------")

m = e.new_message(
    eezo_id=os.environ["DEMO_EEZO_ID"],
    thread_id=os.environ["DEMO_THREAD_ID"],
    context="test",
)

m.add("text", text="Hello, world!")
m.notify()


time.sleep(3)

m = e.update_message(m.id)
m.add("text", text="Hello, world! Updated!")
m.notify()

time.sleep(3)

e.delete_message(m.id)

thread = e.get_thread(
    eezo_id=os.environ["DEMO_EEZO_ID"],
    thread_id=os.environ["DEMO_THREAD_ID"],
)

print(thread)


try:
    e.create_agent(
        agent_id="demo-2",
        description="Invoke when user says demo 2 or demo agent 2",
        environment_variables=[{"key": "test", "value": "deed"}],
    )
except Exception as error:
    print(error)


def invoke(c: Context, num_executions):
    def invoke_query(i):
        return c.invoke("demo-1", query=f"--- {i}")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(invoke_query, i) for i in range(num_executions)]
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]
        return results


@e.on("demo-1")
def chart_demo(c: Context, **kwargs):
    print("Chart demo")
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
    return {"status": "success", "test": f"test {kwargs.get('query')}"}


@e.on("demo-2")
def invoke_demo(c: Context, **kwargs):
    print("Invoke demo")
    print(c.environment_variables)
    m = c.new_message()
    m.add("text", text=f"Env: {c.environment_variables}")
    m.add_new_line()
    m.add("text", text="Hello, world 2")
    thread_str = c.get_thread(to_string=True)
    m.add("text", text=f"```{thread_str}```")
    thread_str = c.get_thread()
    m.add("text", text=f"```{thread_str}```")
    m.notify()

    results = invoke(c, 2)
    m.add("text", text=f"Result from Agent 1: {results}")
    m.notify()
    print("Invoke demo-1")
    c.invoke_async("demo-1", query="Async call")
    print("Invoked demo-1")
    m.add("text", text="Async call sent")
    m.notify()


e.connect()
