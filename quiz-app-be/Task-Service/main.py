from typing import List

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware

from configs.socket_manager import ConnectionManager
from routers.task_router import router as task_router
from constants import FAPP_PORT

app = FastAPI()

app.include_router(task_router)


# config port and host
# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=int(FAPP_PORT))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
