from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import subprocess
import os

app = FastAPI()

# In-memory store for passwords (demo only) - in prod use DB
user_passwords = {}

class UserRequest(BaseModel):
    username: str
    password: str
    display_name: str

@app.post("/create-user")
async def create_user(user: UserRequest):
    # Validate input
    if not user.username.isdigit() or len(user.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be a number (min 3 digits)")

    # Run the shell script
    try:
        subprocess.run(
            ["./add_extension.sh", user.username, user.password, user.display_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Store password for provisioning endpoint
        user_passwords[user.username] = user.password
        
        public_ip = os.getenv("PUBLIC_IP", "localhost")
        
        # Generate Linphone Provisioning URL
        # Note: Linphone expects this URL to return the XML config
        provisioning_url = f"http://{public_ip}:8000/provisioning/{user.username}"
        qr_data = f"linphone-config://{public_ip}:8000/provisioning/{user.username}"
        
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

@app.get("/provisioning/{username}")
async def get_provisioning(username: str):
    if username not in user_passwords:
        # Fallback: try to find user in config or just fail. 
        # For demo, if restart happens, memory is lost. 
        # We'll assume a default password or fail.
        raise HTTPException(status_code=404, detail="User not found or restart occurred")
    
    password = user_passwords[username]
    public_ip = os.getenv("PUBLIC_IP", "localhost")
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<config xmlns="http://www.linphone.org/xsds/lpconfig.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.linphone.org/xsds/lpconfig.xsd lpconfig.xsd">
  <section name="proxy_0">
    <entry name="reg_proxy" value="sip:{public_ip};transport=udp"/>
    <entry name="reg_route" value="sip:{public_ip};transport=udp"/>
    <entry name="reg_identity" value="sip:{username}@{public_ip}"/>
    <entry name="reg_expires" value="3600"/>
    <entry name="reg_sendregister" value="1"/>
    <entry name="publish" value="0"/>
  </section>
  <section name="auth_info_0">
    <entry name="username" value="{username}"/>
    <entry name="passwd" value="{password}"/>
    <entry name="realm" value="asterisk"/>
    <entry name="domain" value="{public_ip}"/>
  </section>
</config>
"""
    return Response(content=xml_content, media_type="application/xml")
