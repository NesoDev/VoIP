from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import websockets
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIPProxy")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/sip-proxy")
async def sip_proxy(client_ws: WebSocket):
    await client_ws.accept()
    logger.info("Client connected to SIP Proxy")
    
    # Target 3CX Server (Hardcoded for this demo based on user input, or dynamic)
    # Ideally, we could pass this as a query param, but for safety/simplicity we hardcode or default
    target_url = "wss://1453.3cx.cloud/sip" 
    
    try:
        # Connect to 3CX with spoofed Origin
        async with websockets.connect(
            target_url, 
            subprotocols=["sip"], 
            origin="https://1453.3cx.cloud"
        ) as server_ws:
            logger.info(f"Connected to 3CX: {target_url}")
            
            async def forward_client_to_server():
                try:
                    while True:
                        data = await client_ws.receive_text()
                        logger.debug(f"Client -> Server: {data}")
                        await server_ws.send(data)
                except Exception as e:
                    logger.error(f"Client->Server Error: {e}")

            async def forward_server_to_client():
                try:
                    while True:
                        data = await server_ws.recv()
                        logger.debug(f"Server -> Client: {data}")
                        await client_ws.send_text(data)
                except Exception as e:
                    logger.error(f"Server->Client Error: {e}")

            # Run both forwarders concurrently
            await asyncio.gather(
                forward_client_to_server(),
                forward_server_to_client()
            )
            
    except Exception as e:
        logger.error(f"Proxy Error: {e}")
        await client_ws.close()

# Serve Frontend Static Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
