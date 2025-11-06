#!/bin/bash
while true; do
    if [[ -f ~/intermediate.json ]]; then
        python3 reducer.py
        rm ~/intermediate.json
    fi
    sleep 5
done