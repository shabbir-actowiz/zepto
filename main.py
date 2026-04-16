from fastapi import FastAPI
from parser import *

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to the search suggestion API of Zepto!"}

@app.get("/search/{query}")
def search(query):
    return get_search_suggestion(query)