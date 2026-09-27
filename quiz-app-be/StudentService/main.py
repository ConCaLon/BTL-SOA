import uvicorn
from fastapi import FastAPI
from routers.student_router import router as student_router
from starlette.middleware.cors import CORSMiddleware
from constants import FAPP_PORT

app = FastAPI(title="Student Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=int(FAPP_PORT or 8003), reload=True)
