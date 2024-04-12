from .interface import Interface, AsyncInterface

import traceback
import logging
import asyncio
import socketio
import aiohttp
import requests
import time
import os

SERVER = "https://api-service-bofkvbi4va-ey.a.run.app"
if os.environ.get("EEZO_DEV_MODE") == "True":
    SERVER = "http://localhost:8082"

API_VERSION = "/v1"
REST_AUTH_URL = "/signin/"


class JobCompleted:
    def __init__(self, result, success, error=None, traceback=None, error_tag=None):
        self.result = result
        self.success = success
        self.error = error
        self.traceback = traceback
        self.error_tag = error_tag

    def to_dict(self):
        return {
            "result": self.result,
            "success": self.success,
            "error": self.error,
            "traceback": self.traceback,
            "error_tag": self.error_tag,
        }


class AsyncConnector:
    def __init__(self, api_key, connector_id, connector_function, logger=False):
        self.api_key = api_key
        self.logger = logger
        self.func = connector_function
        self.connector_id = connector_id
        self.job_responses = {}
        self.user_id = None
        self.run_loop = True

        if logger:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        self.sio = socketio.AsyncClient(
            reconnection_attempts=0,
            reconnection_delay_max=10,
            reconnection_delay=1,
            engineio_logger=False,
            logger=False,
        )

        @self.sio.event
        async def connect():
            await self.sio.emit(
                "authenticate",
                {
                    "token": self.auth_token,
                    "cid": self.connector_id,
                    "key": self.api_key,
                },
            )
            self.__log(f" ✔ Connector {self.connector_id} connected")

    def __log(self, message):
        if self.logger:
            logging.info(message)

    async def __authenticate(self):
        async with aiohttp.ClientSession() as session:
            url = f"{SERVER}{API_VERSION}{REST_AUTH_URL}"
            async with session.post(url, json={"api_key": self.api_key}) as response:
                if response.status == 200:
                    resp_json = await response.json()
                    self.auth_token = resp_json.get("token")
                    self.user_id = resp_json.get("user_id")
                else:
                    resp_json = await response.json()
                    raise Exception(f"{response.status}: {resp_json['detail']}")

    async def __get_job_result(self, job_id):
        while job_id not in self.job_responses:
            await asyncio.sleep(0.1)
        response = self.job_responses.pop(job_id)
        self.__log(f"<< Sub Job {job_id} completed")
        if not response.get("success", True):
            self.__log(f" ✖ Sub Job {response['id']} failed:\n{response['traceback']}.")
            raise Exception(
                f"Propagating error from sub job {job_id}: {response['error']}"
            )
        return response["result"]

    async def __execute_job(self, job_obj):
        job_id, connector_id, payload = (
            job_obj["job_id"],
            job_obj["connector_id"],
            job_obj["job_payload"],
        )
        self.__log(
            f"<< Job for connector {connector_id} received with payload: {payload}"
        )
        try:
            # Create an interface object that the connector function can use to interact with the Eezo server
            i = AsyncInterface(
                job_id=job_id,
                user_id=self.user_id,
                api_key=self.api_key,
                cb_send_message=lambda p: self.sio.emit("direct_message", p),
                cb_invoke_connector=lambda p: self.sio.emit("invoke_skill", p),
                cb_get_result=self.__get_job_result,
            )
            result = await self.func(i, **payload)
            await self.sio.emit("job_completed", JobCompleted(result, True).to_dict())
        except Exception as e:
            self.__log(f" ✖ Connector {connector_id} failed:\n{traceback.format_exc()}")
            job_completed = JobCompleted(
                result=None,
                success=False,
                error=str(e),
                traceback=traceback.format_exc(),
                error_tag="Connector error",
            )
            await self.sio.emit("job_completed", job_completed.to_dict())

    async def __handle_disconnect(self):
        self.__log(f" ✖ Connector {self.connector_id} disconnected")
        # Additional logic to determine if reconnect should be attempted
        # For example, check if it was an expected disconnection or if a maximum number of retries has been reached
        await self.__attempt_connect()

    async def connect(self):
        await self.__authenticate()

        self.sio.on("disconnect", self.__handle_disconnect)

        def auth_error(message: str):
            self.__log(f" ✖ Authentication failed: {message}")
            self.run_loop = False

        async def job_response(response):
            self.job_responses[response["id"]] = response

        async def on_job_request(p):
            await self.__execute_job(p)

        async def on_token_expired():
            await self.__authenticate()

        self.sio.on("job_request", on_job_request)
        self.sio.on("job_response", job_response)
        self.sio.on("token_expired", on_token_expired)
        self.sio.on("auth_error", auth_error)

        await self.__attempt_connect()

    async def __attempt_connect(self, retry_delay=5, max_retries=10):
        retries = 0
        while self.run_loop and retries < max_retries:
            try:
                await self.sio.connect(SERVER)
                await self.sio.wait()
                break  # Exit loop if connect is successful
            except (socketio.exceptions.ConnectionError, Exception) as e:
                self.__log(
                    f" ✖ Connector {self.connector_id} failed to connect with error: {e}"
                )
                await asyncio.sleep(retry_delay)
                retries += 1
                if retries >= max_retries:
                    self.__log("Reached maximum retries, stopping.")
                    self.run_loop = False
            except KeyboardInterrupt:
                self.__log("Manual interrupt, stopping.")
                self.run_loop = False
                break

        if not self.run_loop:
            await self.sio.disconnect()


class Connector:
    def __init__(self, api_key, connector_id, connector_function, logger=False):
        self.api_key = api_key
        self.logger = logger
        self.func = connector_function
        self.connector_id = connector_id
        self.job_responses = {}
        self.user_id = None
        self.run_loop = True

        if logger:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        self.sio = socketio.Client(
            reconnection_attempts=0,
            reconnection_delay_max=10,
            reconnection_delay=1,
            engineio_logger=False,
            logger=False,
        )

        @self.sio.event
        def connect():
            self.sio.emit(
                "authenticate",
                {
                    "token": self.auth_token,
                    "cid": self.connector_id,
                    "key": self.api_key,
                },
            )
            self.__log(f" ✔ Connector {self.connector_id} connected")

    def __log(self, message):
        if self.logger:
            logging.info(message)

    def __authenticate(self):
        url = f"{SERVER}{API_VERSION}{REST_AUTH_URL}"
        response = requests.post(url, json={"api_key": self.api_key})
        if response.status_code == 200:
            self.auth_token = response.json().get("token")
            self.user_id = response.json().get("user_id")
        else:
            raise Exception(f"{response.status_code}: {response.json()['detail']}")

    def __get_job_result(self, job_id):
        while True:
            if job_id in self.job_responses:
                response = self.job_responses.pop(job_id)
                self.__log(f"<< Sub Job {job_id} completed.")

                if not response.get("success", True):
                    self.__log(
                        f" ✖ Sub Job {response['id']} failed:\n{response['traceback']}."
                    )
                    raise Exception(response["error"])

                return response["result"]
            else:
                time.sleep(0.1)

    def __execute_job(self, job_obj):
        job_id, connector_id, payload = (
            job_obj["job_id"],
            job_obj["connector_id"],
            job_obj["job_payload"],
        )
        self.__log(
            f"<< Job for connector {connector_id} received with payload: {payload}"
        )
        try:
            # Create an interface object that the connector function can use to interact with the Eezo server
            i = Interface(
                job_id=job_id,
                user_id=self.user_id,
                api_key=self.api_key,
                cb_send_message=lambda p: self.sio.emit("direct_message", p),
                cb_invoke_connector=lambda p: self.sio.emit("invoke_skill", p),
                cb_get_result=self.__get_job_result,
            )
            # Call the connector function with the interface object and the job payload
            result = self.func(i, **payload)
            self.sio.emit("job_completed", JobCompleted(result, True).to_dict())
        except Exception as e:
            self.__log(f" ✖ Connector {connector_id} failed:\n{traceback.format_exc()}")
            job_completed = JobCompleted(
                result=None,
                success=False,
                error=str(e),
                traceback=str(traceback.format_exc()),
                error_tag="Connector error",
            )
            self.sio.emit("job_completed", job_completed.to_dict())

    def __handle_disconnect(self):
        self.__log(f" ✖ Connector {self.connector_id} disconnected")
        # Additional logic to determine if reconnect should be attempted
        # For example, check if it was an expected disconnection or if a maximum number of retries has been reached
        self.__attempt_connect()

    def connect(self):
        self.__authenticate()

        self.sio.on("disconnect", self.__handle_disconnect)

        def auth_error(message: str):
            self.__log(f" ✖ Authentication failed: {message}")
            self.run_loop = False

        def job_response(response):
            self.job_responses[response["id"]] = response

        self.sio.on("job_request", lambda p: self.__execute_job(p))
        self.sio.on("job_response", job_response)
        self.sio.on("token_expired", lambda: self.__authenticate())
        self.sio.on("auth_error", auth_error)

        self.__attempt_connect()

    def __attempt_connect(self, retry_delay=5, max_retries=10):
        retries = 0
        while self.run_loop and retries < max_retries:
            try:
                self.sio.connect(SERVER)
                self.sio.wait()
                break  # Exit loop if connect is successful
            except (socketio.exceptions.ConnectionError, Exception) as e:
                self.__log(
                    f" ✖ Connector {self.connector_id} failed to connect with error: {e}"
                )
                time.sleep(retry_delay)
                retries += 1
                if retries >= max_retries:
                    self.__log("Reached maximum retries, stopping.")
                    self.run_loop = False
            except KeyboardInterrupt:
                self.__log("Manual interrupt, stopping.")
                self.run_loop = False
                break

        if not self.run_loop:
            self.sio.disconnect()
