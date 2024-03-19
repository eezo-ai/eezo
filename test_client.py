from eezo import Eezo

import dotenv
import time
import os

dotenv.load_dotenv()

e = Eezo(logger=True)

# Send a message to the Chat UI
m = e.new_message(
    eezo_id=os.environ["DEMO_EEZO_ID"],
    thread_id=os.environ["DEMO_THREAD_ID"],
    context="test",
)

m.add("text", text="Hello, world!")
m.notify()

time.sleep(3)

# Update the message in Chat UI
m = e.update_message(m.id)
m.add("text", text="Hello, world! Updated!")
m.notify()

time.sleep(3)

# Delete the message from Chat UI
e.delete_message(m.id)


@e.on(os.environ["DEMO_AGENT_ID"])
def chart_demo(server, **kwargs):
    m = server.new_message()
    m.add(
        "chart",
        chart_type="candlestick",
        data=[[10, 15, 5, 12], [11, 13, 9, 8], [12, 12, 10, 11]],
        xaxis=["a", "b", "c"],
        name="Example chart",
        chart_title="Example chart",
    )
    m.notify()

    # result = server.get_thread()

    # formatted_json = json.dumps(result, indent=4)
    # m.add("text", text=f"```{formatted_json}```")
    # m.notify()


e.connect()
