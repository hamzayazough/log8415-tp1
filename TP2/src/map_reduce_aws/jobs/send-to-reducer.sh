#!/bin/bash
while true; do
    if [[ -f ~/intermediate.json ]]; then
        scp -i Reducer.pem -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r ~/intermediate.json ubuntu@HOST_PUBLIC_IP_ADDRESS:~
        rm ~/intermediate.json
    fi
    sleep 5
done