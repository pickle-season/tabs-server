from fastapi import FastAPI

from app.models import Song
from app.server import TabsServer
from app.utils import APIResponse, LoginData

app = FastAPI(title="Tabs Server")
server = TabsServer()

@app.get("/chords/{chords_id}")
async def chords(chords_id: int):
    return server.get_chords(chords_id)

@app.get("/tab/{tab_id}")
async def tab(tab_id: int):
    return server.get_tab(tab_id)

@app.get("/saved_songs")
async def saved_songs():
    return server.get_songs()

@app.post("/update")
async def update(login_data: LoginData) -> APIResponse:
    # TODO: Uncomment
    #try:
    await server.update_songs(login_data)

    #except Exception as error:
        #return APIResponse("error", str(error))

    return APIResponse("ok", "test")
