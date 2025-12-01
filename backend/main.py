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
        
        # Store password and display name for provisioning endpoint
        user_passwords[user.username] = {
            "password": user.password,
            "display_name": user.display_name
        }
        
        public_ip = os.getenv("PUBLIC_IP", "localhost")
        
        # Generate Linphone Provisioning URL
        # Using port 3000 (Nginx) is safer than 8000 to avoid firewall issues.
        # Nginx proxies /api/ to backend:8000/
        provisioning_url = f"http://{public_ip}:3000/api/provisioning/{user.username}"
        qr_data = provisioning_url
        
        return {
            "status": "success",
            "message": f"Extension {user.username} created!",
            "data": {
                "username": user.username,
                "password": user.password,
                "display_name": user.display_name,
                "domain": public_ip,
                "transport": "UDP",
                "qr_code_text": qr_data
            }
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Script failed: {e.stderr}")

def recover_user_from_config(username: str):
    """Recover password and display_name from pjsip_custom.conf if memory is lost."""
    try:
        with open("add_extension.sh", "r") as f: # Dummy check to ensure we are in right dir
            pass
            
        config_path = "asterisk/pjsip_custom.conf"
        # In Docker, the path is mapped to /etc/asterisk, but we are running from /app
        # and the volume is ./asterisk -> /etc/asterisk.
        # Wait, inside the container, the script writes to /etc/asterisk/pjsip_custom.conf
        # But the python app reads from...?
        # The python app is in /app. The volume is mounted at /etc/asterisk.
        # So we should read /etc/asterisk/pjsip_custom.conf
        
        config_path = "/etc/asterisk/pjsip_custom.conf"
        if not os.path.exists(config_path):
            return None

        with open(config_path, "r") as f:
            content = f.read()
            
        # Simple parsing logic
        # Look for [username]
        # Then look for password=... and callerid="..."
        
        user_section = f"[{username}](endpoint_standard)"
        if user_section not in content:
            return None
            
        # Extract password
        import re
        pass_match = re.search(r"\[auth" + username + r"\]\(auth_user\)\s+username=" + username + r"\s+password=(.+)", content)
        # Regex might be tricky across lines. Let's do line by line.
        
        lines = content.split('\n')
        password = None
        display_name = None
        
        in_auth_section = False
        
        for line in lines:
            line = line.strip()
            if line.startswith(f"callerid="):
                # callerid="Name" <User>
                # Check if this callerid belongs to our user block. 
                # This is a bit weak without full parsing, but for this file structure it works.
                # We assume the callerid line comes shortly after the [username] block start.
                pass
            
            # Better regex approach on full content
            
        # Regex for password in auth section
        # [auth200](auth_user)
        # username=200
        # password=1234
        pass_pattern = re.compile(r"\[auth" + username + r"\]\(auth_user\)\s*\n\s*username=" + username + r"\s*\n\s*password=(.*)", re.MULTILINE)
        pass_match = pass_pattern.search(content)
        if pass_match:
            password = pass_match.group(1).strip()
            
        # Regex for display name
        # callerid="nesodev" <200>
        caller_pattern = re.compile(r"\[" + username + r"\]\(endpoint_standard\).*?callerid=\"(.*?)\"\s*<" + username + r">", re.DOTALL)
        caller_match = caller_pattern.search(content)
        if caller_match:
            display_name = caller_match.group(1).strip()
            
        if password and display_name:
            return {"password": password, "display_name": display_name}
            
        return None
    except Exception as e:
        print(f"Error recovering user: {e}")
        return None

@app.get("/provisioning/{username}")
async def get_provisioning(username: str):
    print(f"Provisioning requested for {username}") # Debug log
    
    user_data = None
    if username in user_passwords:
        user_data = user_passwords[username]
    else:
        # Try to recover from file
        print(f"User {username} not in memory, attempting recovery from file...")
        user_data = recover_user_from_config(username)
        
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found (and could not be recovered)")
    
    password = user_data["password"]
    display_name = user_data["display_name"]
    public_ip = os.getenv("PUBLIC_IP", "localhost")
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<config xmlns="http://www.linphone.org/xsds/lpconfig.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.linphone.org/xsds/lpconfig.xsd lpconfig.xsd">
  <section name="proxy_0">
    <entry name="reg_proxy" value="sip:{public_ip};transport=udp"/>
    <entry name="reg_route" value="sip:{public_ip};transport=udp"/>
    <entry name="reg_identity" value="&quot;{display_name}&quot; &lt;sip:{username}@{public_ip}&gt;"/>
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
