from fastapi import FastAPI

app = FastAPI(
        title = "crud store catalog",
        description = "rest api through fastAPI framework",
        version="1.0"
)



@app.get("/")
def root():
    return {'status' : 'ok', 'message' : 'service running...'}



