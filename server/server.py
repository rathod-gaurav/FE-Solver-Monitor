from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

clients = []

html = """
<!DOCTYPE html>
<html>

<head>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
</head>

<body>

<h2>Nonlinear FEM Convergence Monitor</h2>

<div id="plot" style="width:900px;height:500px;"></div>

<script>

var traces = {}
var traceIndices = {}

Plotly.newPlot('plot', [], {
    yaxis: {type:'log', title:'Residual'},
    xaxis: {title:'Newton Iteration'},
    title:'Residual vs Iteration per Increment'
})

var ws = new WebSocket("ws://127.0.0.1:8000/ws")

ws.onopen = function(){
    console.log("WebSocket connected")

    // keep connection alive
    setInterval(function(){
        ws.send("ping")
    }, 1000)
}

ws.onmessage = function(event){

    console.log("Received:", event.data)

    var data = JSON.parse(event.data)

    var incr = data.increment
    var iter = data.iteration
    var res  = data.residual

    if(!(incr in traces)){

        traces[incr] = {x:[], y:[]}

        var trace = {
            x: traces[incr].x,
            y: traces[incr].y,
            mode: 'lines+markers',
            name: 'Increment ' + incr
        }

        Plotly.addTraces('plot', trace)

        traceIndices[incr] = Object.keys(traceIndices).length
    }

    traces[incr].x.push(iter)
    traces[incr].y.push(res)

    Plotly.restyle('plot', {
        x:[traces[incr].x],
        y:[traces[incr].y]
    }, [traceIndices[incr]])

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
            await websocket.receive_text()
    except:
        pass
    finally:
        clients.remove(websocket)



@app.post("/residual")
async def receive_residual(data: dict):

    message = json.dumps(data)

    for client in clients:
        await client.send_text(message)

    return {"status": "ok"}
