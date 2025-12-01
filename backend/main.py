from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os

app = FastAPI()

class UserRequest(BaseModel):
    username: str
    password: str
    display_name: str

@app.post("/create-user")
async def create_user(user: UserRequest):
    # Validate input (basic)
    if not user.username.isdigit() or len(user.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be a number (min 3 digits)")

    # Run the shell script to add the user
    try:
        # Pass arguments to the script
        result = subprocess.run(
            ["./add_extension.sh", user.username, user.password, user.display_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Get the public IP from environment (passed by start.sh)
        public_ip = os.getenv("PUBLIC_IP", "localhost")
        
        # Generate Linphone Config URL (or just return data)
        # Format for QR: <sip:USER:PASS@DOMAIN> is simple but Linphone prefers config XML.
        # For this demo, we return the raw data and a text block for the QR.
        qr_data = f"sip:{user.username}:{user.password}@{public_ip}"
        
        return {
            "status": "success",
            "message": f"Extension {user.username} created!",
            "data": {
                "username": user.username,
                "password": user.password,
                "domain": public_ip,
                "transport": "UDP",
                "qr_code_text": qr_data
            }
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Script failed: {e.stderr}")
