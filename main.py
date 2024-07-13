from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from starlette.requests import Request

app = FastAPI()


# Serve static files (CSS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load HTML templates
templates = Jinja2Templates(directory="templates")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.team_points = {"team1": 0, "team2": 0}
        self.result = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.broadcast_points()

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_points(self):
        data = {
            "team1Points": self.team_points["team1"],
            "team2Points": self.team_points["team2"]
        }
        for connection in self.active_connections:
            await connection.send_json(data)

    async def add_point(self, team: str):
        if team in self.team_points:
            self.team_points[team] += 1
            await self.broadcast_points()




manager = ConnectionManager()

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.add_point(data["team"])
    except WebSocketDisconnect:
        manager.disconnect(websocket)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)