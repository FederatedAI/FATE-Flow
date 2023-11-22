STORAGE_NAME = "s3"
STORAGE_ADDRESS = "s3://127.0.0.1:9000?username=admin&password=12345678"
TRANSPORT = "127.0.0.1:9377"
SESSION_ID = "session_{}"
TOKEN = "session_{}"
FATE_CONTAINER_HOME = "/data/projects/fate/fate_flow"
CONTAINER_LOG_PATH = f"{FATE_CONTAINER_HOME}/logs"
CALLBACK_ADDRESS = "http://127.0.0.1:9380"
CALLBACK = f"{CALLBACK_ADDRESS}/v1/platform/schedule/task/callback"


VOLUME = {
    # "/data/projects/fate/fate_flow/logs": {
    #     'bind': "/data/projects/fate/fate_flow/logs",
    #     'mode': 'rw'
    # }
}
