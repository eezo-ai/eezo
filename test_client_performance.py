from concurrent.futures import ThreadPoolExecutor

import dotenv
import time
import os

dotenv.load_dotenv()

from eezo import Eezo

e = Eezo(logger=True)


def get_human_readable_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))


# Direct message test ---------------------------------------------------------


# def send_messages(i: int):
#     # Send a message to the Chat UI
#     m = e.new_message(
#         eezo_id=os.environ["DEMO_EEZO_ID"],
#         thread_id=os.environ["DEMO_THREAD_ID"],
#         context="test " + str(i),
#     )

#     m.add("text", text="Hello, world " + str(i) + "! " + get_human_readable_time())
#     m.notify()

#     time.sleep(3)

#     # Update the message in Chat UI
#     m = e.update_message(m.id)
#     m.add(
#         "text",
#         text="Hello, world! Updated " + str(i) + "! " + get_human_readable_time(),
#     )
#     m.notify()

#     time.sleep(3)

#     # Delete the message from Chat UI
#     e.delete_message(m.id)


def invoke_demo(c, **kwargs):
    print("Invoke demo")
    m = c.new_message()
    m.add("text", text="Hello, world 2")
    m.notify()


for i in range(20):
    e.add_connector(os.environ["DEMO_AGENT_ID_2"], invoke_demo)

e.connect()
