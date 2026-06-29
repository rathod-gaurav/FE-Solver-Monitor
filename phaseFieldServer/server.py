from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import json

app = FastAPI()
clients = []

# HTML/JS Frontend with two subplots
html = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
</head>
<body>
    <h2>Solidification 1D: Phase (\u03c6) and Temperature (T)</h2>
    <div id="plot_phi" style="width:900px;height:400px;"></div>
    <div id="plot_T" style="width:900px;height:400px;"></div>

    <script>
        // Initialize two plots
        Plotly.newPlot('plot_phi', [{x:[], y:[], name: '\u03c6'}], {title: 'Phase Field (\u03c6)', xaxis: {title: 'x'}, yaxis: {title: '\u03c6'}});
        Plotly.newPlot('plot_T', [{x:[], y:[], name: 'T', line: {color: 'red'}}], {title: 'Temperature (T)', xaxis: {title: 'x'}, yaxis: {title: 'T'}});

        var ws = new WebSocket("ws://127.0.0.1:8000/ws");

        ws.onmessage = function(event) {
            var data = JSON.parse(event.data);
            
            // Update phi plot
            Plotly.react('plot_phi', [{x: data.x, y: data.phi, name: '\u03c6'}], {title: 'Phase Field (\u03c6) - Time: ' + data.time.toFixed(4)});
            
            // Update T plot
            Plotly.react('plot_T', [{x: data.x, y: data.T, name: 'T', line: {color: 'red'}}], {title: 'Temperature (T) - Time: ' + data.time.toFixed(4)});
        };
    </script>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    finally:
        clients.remove(websocket)

@app.post("/update")
async def receive_data(data: dict):
    message = json.dumps(data)
    for client in clients:
        await client.send_text(message)
    return {"status": "ok"}