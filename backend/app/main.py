from fastapi import FastAPI

app = FastAPI(title="Skill Swipe API")


@app.get("/")
def read_root():
    return {"message": "Skill Swipe API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
