# VoIP Demo

Educational VoIP demonstration with detailed SIP protocol logging.

## Overview

This application demonstrates Session Initiation Protocol (SIP) communication flow through real-time detailed logging. Built for Networks and Data Transmission courses.

## Features

- Complete SIP server implementation (pyVoIP)
- Real-time WebSocket logging
- Automatic internal IP assignment
- Heartbeat-based presence system
- Web-based interface

## Quick Start

### Using Docker

```bash
./start.sh
```

Access: http://localhost:3000

### Manual Setup

Backend:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Frontend (any HTTP server):
```bash
cd frontend
python3 -m http.server 3000
```

## Architecture

```
Browser (HTML/CSS/JS)
    ↓ HTTP/WebSocket
FastAPI Backend
    ├─ User Manager
    └─ SIP Server (UDP:5060)
```

## Network Ports

| Port | Protocol | Service |
|------|----------|---------|
| 3000 | TCP | Frontend |
| 8000 | TCP | Backend API |
| 5060 | UDP | SIP Signaling |
| 10000-10100 | UDP | RTP Audio |

## SIP Protocol Flow

1. REGISTER - User registration
2. 200 OK - Registration confirmed
3. INVITE - Call initiation with SDP
4. 100 TRYING - Processing
5. 180 RINGING - Alerting
6. 200 OK - Call accepted
7. ACK - Session established
8. RTP Session - Audio transmission
9. BYE - Termination request
10. 200 OK - Confirmed

## API Endpoints

```
POST /register          Register user
POST /heartbeat         Update presence  
GET  /users             List active users
GET  /logs              Retrieve logs
POST /call/initiate     Start call
WS   /ws/logs          Real-time updates
```

## AWS Lightsail Deployment

1. Create Ubuntu 22.04 instance ($5/month)
2. Configure firewall ports: 3000, 8000, 5060, 10000-10100
3. Install Docker:
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
```
4. Install Docker Compose:
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```
5. Deploy:
```bash
./start.sh
```

Access via: http://YOUR_PUBLIC_IP:3000

## Technical Details

### Audio Codecs
- G.711 µ-law (PCMU) - 64 kbps
- G.711 A-law (PCMA) - 64 kbps
- Sampling: 8000 Hz
- Packetization: 20ms

### Session Management
- Internal IPs: 192.168.100.x
- Heartbeat interval: 10s
- Timeout: 30s

## Usage

1. Open web interface
2. Enter username
3. System assigns internal IP
4. View connected users
5. Initiate call
6. Observe SIP protocol logs

## Educational Value

Demonstrates:
- SIP message flow (RFC 3261)
- SDP negotiation (RFC 4566)
- RTP protocol (RFC 3550)
- Session establishment
- User presence management

## Limitations

Educational demo with limitations:
- Audio transmission not fully implemented
- No NAT traversal (STUN/TURN)
- No encryption (TLS/SRTP)
- Basic authentication

## Technologies

**Backend:**
- Python 3.11
- FastAPI
- pyVoIP
- aiortc

**Frontend:**
- HTML5
- CSS3
- Vanilla JavaScript

**Infrastructure:**
- Docker
- nginx

## Project Structure

```
voip-demo/
├── backend/
│   ├── main.py
│   ├── sip_server.py
│   ├── user_manager.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── start.sh
└── README.md
```

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart
docker-compose restart

# Rebuild
docker-compose build
```

## Troubleshooting

**Services not starting:**
```bash
docker-compose logs
```

**Port conflicts:**
```bash
sudo lsof -i :3000
sudo lsof -i :8000
```

**WebSocket issues:**
Check API_BASE and WS_BASE in app.js

**SIP not working:**
Verify port 5060 is UDP protocol

## References

- RFC 3261: SIP Protocol
- RFC 4566: SDP
- RFC 3550: RTP
- pyVoIP Documentation

## License

MIT License - Educational Use
