#!/bin/bash
N=${N_INSTANCES:-1}

while true; do
    all_found=true
    for i in $(seq 1 $N); do
        if [[ ! -f "$HEC2/intermediate-$i.msgpack.zst" ]]; then
            all_found=false
            break
        fi
    done

    if [[ "$all_found" == true ]]; then
        echo "All $N intermediate files found — processing..."
        ls "$HEC2/"        
        python3 "$HEC2/reducer.py"
        rm "$HEC2"/intermediate-{1..$N}.msgpack.zst 2>/dev/null
        echo "Processing done, waiting for next batch..."
    fi

    sleep 5
done