; --- Transports ---
; UDP Transport (Standard SIP for Linphone/Zoiper)
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060
; local_net=192.168.0.0/16
local_net=172.16.0.0/12
local_net=10.0.0.0/8
external_media_address=EXTERNAL_IP_PLACEHOLDER
external_signaling_address=EXTERNAL_IP_PLACEHOLDER

; WebSocket Transport (For WebRTC)
[transport-ws]
type=transport
protocol=ws
bind=0.0.0.0:8088
external_media_address=EXTERNAL_IP_PLACEHOLDER
external_signaling_address=EXTERNAL_IP_PLACEHOLDER

; --- Templates ---
; Standard Endpoint (For Linphone)
[endpoint_standard](!)
type=endpoint
context=from-internal
disallow=all
allow=ulaw
direct_media=no
force_rport=yes
rewrite_contact=yes
rtcp_mux=no
identify_by=username

; Auth Template
[auth_user](!)
type=auth
auth_type=userpass
password=1234
realm=asterisk

; AOR Template
[aor_dynamic](!)
type=aor
max_contacts=5
remove_existing=yes
qualify_frequency=60


; --- Dynamic Users ---
#include pjsip_custom.conf
