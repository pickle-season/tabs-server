from fastapi import FastAPI

from app.models import Song
from app.server import TabsServer
from app.utils import APIResponse, LoginData

app = FastAPI(title="Tabs Server")
server = TabsServer()

@app.get("/saved_songs")
async def saved_songs() -> list[Song]:
    return server.get_songs()

@app.post("/update")
async def update(login_data: LoginData) -> APIResponse:
    try:
        await server.update_songs(login_data)

    except Exception as error:
        return APIResponse("error", str(error))

    return APIResponse("ok", "test")
