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
[identify$USERNAME]
type=identify
endpoint=$USERNAME
match=$USERNAME
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
