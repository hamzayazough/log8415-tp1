#!/bin/bash
while true; do
    if [[ -f ~/friendList.txt ]]; then
        python3 mapper.py
        rm ~/friendList.txt
    fi
    sleep 5
done