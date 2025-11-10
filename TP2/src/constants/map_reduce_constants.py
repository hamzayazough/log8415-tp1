## Documentation:
# export HEC2 is used to define the home directory of the ec2-user in the instance
# sed script is used to replace the placeholder HOST_PUBLIC_IP_ADDRESS in the send-to-reducer.sh script with the actual IP address of the reducer instance
# nohup command is used to run the send-to-reducer.sh script in the background, redirecting its output to /dev/null to avoid cluttering the terminal
MAPPER_SENDING_SCRIPT = '''#!/bin/bash
set -e
export HEC2=/home/ec2-user

sed -i 's/HOST_PUBLIC_IP_ADDRESS/{ip1}/g' $HEC2/send-to-reducer.sh
nohup $HEC2/send-to-reducer.sh >> $HEC2/sender.log 2>>$HEC2/sender-error.log &
'''


## Documentation
# purpose: running automatically when EC2 instance starts
# What it does:
# 1. Creates mapper.sh script that continuously checks for friendList.txt file, processes it using mapper.py, and deletes the file after processing
# 2. Creates send-to-reducer.sh script that continuously checks for intermediate.json file, sends it to the reducer instance using scp, and deletes the file after sending
# 3. Creates mapper.py script that contains the same mapper logic as the local version, reading friendList.txt, processing it, and writing intermediate.json
MAPPER_USER_DATA_SCRIPT = '''#!/bin/bash
set -e

export HEC2=/home/ec2-user

cat > $HEC2/mapper.sh <<EOL
#!/bin/bash
while true; do
    if [[ -f $HEC2/friendList.txt ]]; then
        echo "Found friendList.txt | waiting for complete upload"
        ls -l $HEC2/friendList.txt
        sleep 10
        ls -l $HEC2/friendList.txt
        python3 $HEC2/mapper.py
        ls $HEC2/ -la
        rm $HEC2/friendList.txt
    fi
    sleep 5
done
EOL

cat > $HEC2/send-to-reducer.sh <<EOL
#!/bin/bash
while true; do
    if [[ -f $HEC2/intermediate-INSTANCE_NUMBER.msgpack.zst ]]; then
        echo "Sending intermediate-INSTANCE_NUMBER.msgpack.zst"
        ls $HEC2/ -la
        scp -i $HEC2/tp2.pem -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $HEC2/intermediate-INSTANCE_NUMBER.msgpack.zst ec2-user@HOST_PUBLIC_IP_ADDRESS:$HEC2/
        rm $HEC2/intermediate-INSTANCE_NUMBER.msgpack.zst
    fi
    sleep 5
done
EOL

cat > $HEC2/mapper.py <<EOL
from collections import defaultdict
import json
import msgpack
import zstandard as zstd

Data = dict[str, list[str]]
MappedData = list[tuple[str, tuple[str, str]]]
GroupedData = defaultdict[str, list[tuple[str,str]]]

def mapper(data: Data) -> MappedData:
    mapped: MappedData = []

    for user, friends in data.items():
        #direct friends generation
        for f in friends:
            mapped.append((user, ("DIRECT", f)))
            mapped.append((f, ("DIRECT", user)))

        #friends-of-friends generation
        for f in friends:
            fof_list = { x for x in friends if x != f }
            if fof_list:
                mapped.append((f, ("FOF", tuple(fof_list))))

    return mapped


def shuffle(mapped: MappedData) -> GroupedData:
    grouped: GroupedData = defaultdict(set)  # we dont want the same key appearing multiple times
    for key, value in mapped:
        grouped[key].add(value)
    grouped = { k:list(v) for k, v in grouped.items()}
    return grouped

def main():
    try:       
        data: Data = {}

        with open("$HEC2/friendList.txt", "r") as f:
            for line in f:
                line = line.strip()
                
                if not line:
                    print("Line Data Error:", repr(line))
                    continue
                
                parts = line.split()
                
                if len(parts) == 1:
                    user = parts[0]
                    data[user] = []
                    continue
                
                if len(parts) != 2:
                    print("Spliting Data Error:", repr(line))
                    continue

                user, friends_str = parts
                friends_list = friends_str.split(",")

                data[user] = friends_list                
           
        
        mapped: MappedData = mapper(data)
        grouped: GroupedData = shuffle(mapped)
        
        packed = msgpack.packb(grouped)
        compressed = zstd.ZstdCompressor(level=10).compress(packed)

        with open("$HEC2/intermediate-INSTANCE_NUMBER.msgpack.zst", "wb") as f:
            f.write(compressed)
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()

EOL

chmod +x $HEC2/mapper.sh $HEC2/send-to-reducer.sh

sudo yum install python-pip -y
pip install msgpack zstandard


nohup $HEC2/mapper.sh >> $HEC2/mapper.log 2>>$HEC2/mapper-error.log &
'''
## Documentation
# purpose: running automatically when EC2 instance starts
# What it does:
# 1. Creates reducer.sh script that continuously checks for intermediate.json file, processes it using reducer.py, and deletes the file after processing
# 2. Creates reducer.py script that contains the same reducer logic as the local version,
#    reading intermediate.json, processing it, and writing recommendations.txt
REDUCER_USER_DATA_SCRIPT = '''#!/bin/bash
set -e
export HEC2=/home/ec2-user

cat > $HEC2/reducer.sh <<EOL
#!/bin/bash
N=INSTANCE_NUMBER

while true; do
    all_found=true
    for i in \$(seq 1 \$N); do
        if [[ ! -f "$HEC2/intermediate-\$i.msgpack.zst" ]]; then
            all_found=false
            break
        fi
    done

    if [[ "\$all_found" == true ]]; then
        echo "All \$N intermediate files found — processing..."
        ls "$HEC2/" -l
        sleep 20
        ls "$HEC2/" -la
        python3 "$HEC2/reducer.py"
        rm "$HEC2"/intermediate-{1..\$N}.msgpack.zst 2>/dev/null
        echo "Processing done, waiting for next batch..."
    fi

    sleep 5
done
EOL

cat > $HEC2/reducer.py <<EOL
from collections import defaultdict
import json
import msgpack
import zstandard as zstd

GroupedData = defaultdict[str, list[tuple[str,str]]]
ReducedData = dict[str, list[str]]

def reducer(grouped: GroupedData, N=10) -> ReducedData:
    results: ReducedData = {}

    for user, values in grouped.items():
        direct: set[str] = set()
        fof_lists: list[str] = []

        for vtype, value in values:
            if vtype == "DIRECT":
                direct.add(value)
            elif vtype == "FOF":
                fof_lists.append(value)

        # Count mutual friends
        mutual_counts: defaultdict[str,int] = defaultdict(int)
        for fof_group in fof_lists:
            for candidate in fof_group:
                if candidate != user and candidate not in direct:
                    mutual_counts[candidate] += 1

        # Take top N recommendations
        topN = sorted(mutual_counts.items(), key=lambda x: (-x[1], int(x[0])))[:N]

        results[user] = [uid for uid, _ in topN]

    return results


def merge_dicts(*dicts):
    merged = defaultdict(list)
    for d in dicts:
        for key, values in d.items():
            merged[key].extend(values)
    return dict(merged)    

def main():
    try:
        groups = []
        for i in range(1, INSTANCE_NUMBER + 1):
            with open(f"$HEC2/intermediate-{i}.msgpack.zst", "rb") as f:
                compressed = f.read()
                grouped = msgpack.unpackb(zstd.ZstdDecompressor().decompress(compressed))
                groups.append(grouped)
                
        grouped = merge_dicts(*groups)

        recommendations: ReducedData = reducer(grouped, N=10)
        
        with open("$HEC2/recommendations.txt", "w") as f:
            for user, recs in recommendations.items():
                recs_str = ",".join([f"{friend}" for friend in recs])
                f.write(f"{user}\\t{recs_str}\\n")
        
        selected_ids = ["924", "8941", "8942", "9019", "9020", "9021", "9022", "9990", "9992", "9993"]
        with open("$HEC2/selected_recommendations.txt", "w") as f:
            for user in selected_ids:
                recs = recommendations.get(user)
                if recs:
                    recs_str = ",".join([f"{friend}" for friend in recs])
                    f.write(f"{user}\\t{recs_str}\\n")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()

EOL

cat > $HEC2/results.py <<EOL
values = []
with open('$HEC2/recommendations.txt', 'r') as f:
    l = [924,8941,8942,9019, 9020, 9021, 9022, 9990, 9992, 9993]
    for line in f.readlines():
        for n in l:
            if line.startswith(str(n) + '\\t'):
                values.append(line)
sorted_values = sorted(values, key=lambda x : int(x.split('\\t')[0]))
with open('$HEC2/results.txt', 'w') as f:
    f.writelines(sorted_values)
EOL

chmod +x $HEC2/reducer.sh

sudo yum install python-pip -y
pip install msgpack zstandard

nohup $HEC2/reducer.sh >> $HEC2/reducer.log 2>>$HEC2/reducer-error.log &

'''


PROJECT_NAME = "map-reduce-tp2"

DEFAULT_AMI_ID = "ami-0bdd88bd06d16ba03" # image containing: Amazon Linux 2, Python3, AWS CLI tools, ...

# MapReduce deployment configuration constants
SSH_KEY_FILE = 'tp2.pem'
SSH_OPTIONS = ['-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']
EC2_USER = 'ec2-user'
EC2_HOME_DIR = '/home/ec2-user'
INSTANCE_TYPE = 't2.large'
FRIEND_LIST_FILE = 'friendList.txt'
SSH_READY_WAIT_TIME = 30  # seconds to wait for SSH daemon to be ready