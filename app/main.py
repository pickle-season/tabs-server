from fastapi import FastAPI, HTTPException

from app.server import TabsServer
from app.utils import LoginData

app = FastAPI(title="Tabs Server")
server = TabsServer()

# TODO: Implement downloading chords to avoid captcha bullshit
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
async def update(login_data: LoginData):
    try:
        await server.update_songs(login_data)

    except HTTPException as error:
        raise error

    # except Exception as error:
    #     raise HTTPException(status_code=500, detail=str(error))

    return {"detail": "ok"}

@app.get("/dl")
async def dl():
    raise HTTPException(403, "Download is not allowed. need to check get_content first.")
    #server._download()

