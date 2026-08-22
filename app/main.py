from fastapi import FastAPI

app = FastAPI(title="DevMatch API")


@app.get("/")
def root():
    return {"message": "DevMatch API is running"}