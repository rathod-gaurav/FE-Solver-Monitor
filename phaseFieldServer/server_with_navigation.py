from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# Stores active WebSocket connections
clients = []

# HTML/JS Frontend with two subplots and navigation
html = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
</head>
<body>
    <h2>Solidification 1D: Phase (\u03c6) and Temperature (T)</h2>
    
    <div style="margin-bottom: 20px;">
        <button onclick="changeFrame(-1)">Previous</button>
        <span id="frameIndicator"> Navigating History </span>
        <button onclick="changeFrame(1)">Next</button>
    </div>

    <div id="plot_phi" style="width:900px;height:400px;"></div>
    <div id="plot_T" style="width:900px;height:400px;"></div>

    <script>
        // Renamed 'history' to 'dataHistory' to avoid conflict with window.history[cite: 11]
        var dataHistory = []; 
        var currentIndex = -1;

        // Initialize two empty plots[cite: 11]
        Plotly.newPlot('plot_phi', [{x:[], y:[], name: '\u03c6'}], {title: 'Phase Field (\u03c6)', xaxis: {title: 'x'}, yaxis: {title: '\u03c6'}});
        Plotly.newPlot('plot_T', [{x:[], y:[], name: 'T', line: {color: 'red'}}], {title: 'Temperature (T)', xaxis: {title: 'x'}, yaxis: {title: 'T'}});

        var ws = new WebSocket("ws://127.0.0.1:8000/ws");

        ws.onmessage = function(event) {
            var data = JSON.parse(event.data);
            dataHistory.push(data); // Using renamed variable to prevent errors[cite: 11]
            
            // If we are at the latest frame, or haven't navigated yet, auto-update[cite: 11]
            if (currentIndex === dataHistory.length - 2 || currentIndex === -1) {
                currentIndex = dataHistory.length - 1;
                updatePlots(dataHistory[currentIndex]);
            }
            document.getElementById('frameIndicator').innerText = " Frame: " + (currentIndex + 1) + " / " + dataHistory.length;
        };

        function updatePlots(data) {
            Plotly.react('plot_phi', [{x: data.x, y: data.phi, name: '\u03c6'}], {title: 'Phase Field (\u03c6) - Time: ' + data.time.toFixed(4)});
            Plotly.react('plot_T', [{x: data.x, y: data.T, name: 'T', line: {color: 'red'}}], {title: 'Temperature (T) - Time: ' + data.time.toFixed(4)});
        }

        function changeFrame(delta) {
            var nextIndex = currentIndex + delta;
            if (nextIndex >= 0 && nextIndex < dataHistory.length) {
                currentIndex = nextIndex;
                updatePlots(dataHistory[currentIndex]);
                document.getElementById('frameIndicator').innerText = " Frame: " + (currentIndex + 1) + " / " + dataHistory.length;
            }
        }
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
            # Keep connection alive[cite: 11]
            await websocket.receive_text()
    finally:
        clients.remove(websocket)

@app.post("/update")
async def receive_data(data: dict):
    # Broadcast received data to all connected WebSocket clients[cite: 11]
    message = json.dumps(data)
    for client in clients:
        await client.send_text(message)
    return {"status": "ok"}