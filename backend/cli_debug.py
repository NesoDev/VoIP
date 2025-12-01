import argparse
import requests
import qrcode
import os
import sys

def create_user_cli():
    parser = argparse.ArgumentParser(description="Create VoIP User via CLI")
    parser.add_argument("username", help="Extension number (e.g. 300)")
    parser.add_argument("password", help="SIP Password")
    parser.add_argument("name", help="Display Name")
    parser.add_argument("--host", default="localhost", help="Backend Host")
    
    args = parser.parse_args()
    
    url = f"http://{args.host}:8000/create-user"
    payload = {
        "username": args.username,
        "password": args.password,
        "display_name": args.name
    }
    
    print(f"Creating user {args.username} at {url}...")
    try:
        r = requests.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        
        if data["status"] == "success":
            print("\n✅ User Created Successfully!")
            print(f"Username: {data['data']['username']}")
            print(f"Password: {data['data']['password']}")
            print(f"Domain:   {data['data']['domain']}")
            print(f"QR Data:  {data['data']['qr_code_text']}")
            
            print("\nScan this QR Code with Linphone:")
            qr = qrcode.QRCode()
            qr.add_data(data['data']['qr_code_text'])
            qr.print_ascii()
        else:
            print(f"❌ Error: {data}")
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("Ensure the backend is running (docker compose up).")

if __name__ == "__main__":
    create_user_cli()
