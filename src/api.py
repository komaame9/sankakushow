from fastapi import FastAPI
import database

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.get("/save")
def read_save(url:str = None):
    if (not url):
        return "None URL, localhost/save?url=$IMAGE_URL"
    db = database.ImageDB()
    ret = db.get_and_save_image(url)
    if ret:
        return f"[OK]: {url}"
    else:
        
        return f"[ERROR]: {url} can not get"


