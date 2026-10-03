from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rooms import router as rooms_router
from transcribe import router as transcribe_router
from translate import router as translate_router

app = FastAPI(title="Minbar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Minbar API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.router.routes.extend(rooms_router.routes)
app.include_router(transcribe_router)
app.include_router(translate_router)