#!/bin/bash

USERNAME=$1
PASSWORD=$2
DISPLAY_NAME=$3

if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
    echo "Usage: ./add_extension.sh <username> <password> <display_name>"
    exit 1
fi

PJSIP_FILE="/etc/asterisk/pjsip_custom.conf"
EXTEN_FILE="/etc/asterisk/extensions_custom.conf"

echo "Adding user $USERNAME..."

# Check if user already exists and remove them to allow update
if grep -q "\[$USERNAME\]" "$PJSIP_FILE"; then
    echo "User $USERNAME exists. Updating..."
    # Remove the user block. 
    # We assume the block starts with [USERNAME] and ends before the next block or EOF.
    # Since our blocks are well formatted with newlines, we can try to remove it.
    # But sed is tricky with multi-line blocks.
    # Simpler approach for this demo: 
    # We will use a python helper or just append to the end and let Asterisk handle it? 
    # No, Asterisk might get confused with duplicate sections.
    
    # Let's use a temporary file approach:
    # Remove lines from [USERNAME] until the next [XXX] or EOF.
    # Actually, since we control the format, we know it ends with a blank line or next section.
    
    # Alternative: Just append to the end. Asterisk 'pjsip' usually takes the last definition or merges?
    # PJSIP does NOT merge endpoints with same name defined twice in same context usually.
    # It's safer to remove.
    
    # Let's use a simple sed command to delete the block. 
    # Assuming standard format:
    # [USERNAME](endpoint_standard)
    # ...
    # [identifyUSERNAME]
    # ...
    # match=USERNAME
    
    # We can delete by matching the start of the block and N lines? No, variable length.
    # Let's use a python one-liner to filter the file, it's more robust than sed for this.
    
    python3 -c "
import sys
import re

user = '$USERNAME'
file_path = '$PJSIP_FILE'

with open(file_path, 'r') as f:
    content = f.read()

# Regex to remove the user block.
# We look for [user](endpoint_standard) ... until [identifyUser] ... match=user
# This covers the whole block we add.
pattern = r'\[{0}\]\(endpoint_standard\).*?match={0}\n'.format(user)
new_content = re.sub(pattern, '', content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(new_content)
"
fi

# 1. Add to PJSIP Config
cat <<EOF >> $PJSIP_FILE

; --- User $USERNAME ---
[$USERNAME](endpoint_standard)
auth=auth$USERNAME
aors=$USERNAME
callerid="$DISPLAY_NAME" <$USERNAME>

[auth$USERNAME](auth_user)
username=$USERNAME
password=$PASSWORD

[$USERNAME](aor_dynamic)
EOF

# 2. Add to Dialplan (Optional, as we use pattern matching _XXX)
# But let's add it for completeness if we wanted specific logic
# echo "exten => $USERNAME,1,Dial(PJSIP/$USERNAME,20)" >> $EXTEN_FILE

# 3. Reload Asterisk via AMI (using netcat)
# AMI Protocol:
# Action: Login
# Username: admin
# Secret: admin1234
#
# Action: Command
# Command: module reload res_pjsip.so
#
# Action: Logoff

# We use a simple python oneliner or nc to send this to asterisk:5038
# Since nc might not be in the slim image, we use python which is there.

python3 -c "
import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('asterisk', 5038))
s.sendall(b'Action: Login\r\nUsername: admin\r\nSecret: admin1234\r\n\r\n')
time.sleep(0.5)
s.sendall(b'Action: Command\r\nCommand: module reload res_pjsip.so\r\n\r\n')
time.sleep(0.5)
s.sendall(b'Action: Logoff\r\n\r\n')
s.close()
"

echo "User $USERNAME added and Asterisk reloaded."
