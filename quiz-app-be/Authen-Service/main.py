import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from router.authen_router import router as authen_router

app = FastAPI()

app.include_router(authen_router)

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
