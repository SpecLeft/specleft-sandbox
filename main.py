from fastapi import FastAPI
from src.database.database import init_db
from src.rules.router import router as rules_router

app = FastAPI(title="Notification Rules Engine API")


@app.on_event("startup")
def startup_event():
    init_db()


app.include_router(rules_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
