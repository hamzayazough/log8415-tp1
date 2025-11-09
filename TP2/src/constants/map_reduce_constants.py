MAPPER_SENDING_SCRIPT = '''#!/bin/bash
set -e
export HEC2=/home/ec2-user

sed -i 's/HOST_PUBLIC_IP_ADDRESS/{ip1}/g' $HEC2/send-to-reducer.sh
nohup $HEC2/send-to-reducer.sh >> $HEC2/sender.log 2>>$HEC2/sender-error.log &
'''


MAPPER_USER_DATA_SCRIPT = '''#!/bin/bash
set -e

export HEC2=/home/ec2-user

cat > $HEC2/mapper.sh <<EOL
#!/bin/bash
while true; do
    if [[ -f $HEC2/friendList.txt ]]; then
        echo "Found FriendList.txt"
        ls $HEC2/
        python3 $HEC2/mapper.py
        ls $HEC2/
        rm $HEC2/friendList.txt
    fi
    sleep 5
done
EOL

cat > $HEC2/send-to-reducer.sh <<EOL
#!/bin/bash
while true; do
    if [[ -f $HEC2/intermediate.msgpack.zst ]]; then
        echo "Sending intermediate.msgpack.zst"
        ls $HEC2/
        scp -i $HEC2/tp2.pem -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $HEC2/intermediate.msgpack.zst ec2-user@HOST_PUBLIC_IP_ADDRESS:$HEC2/
        rm $HEC2/intermediate.msgpack.zst
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
            fof_list = [x for x in friends if x != f]
            if fof_list:
                mapped.append((f, ("FOF", fof_list)))

    return mapped


def shuffle(mapped: MappedData) -> GroupedData:
    grouped: GroupedData = defaultdict(list)
    for key, value in mapped:
        grouped[key].append(value)

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

        with open("$HEC2/intermediate.msgpack.zst", "wb") as f:
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

REDUCER_USER_DATA_SCRIPT = '''#!/bin/bash
set -e
export HEC2=/home/ec2-user

cat > $HEC2/reducer.sh <<EOL
#!/bin/bash
while true; do
    if [[ -f $HEC2/intermediate.msgpack.zst ]]; then
        echo "Processing intermediate.msgpack.zst"
        ls $HEC2/
        python3 $HEC2/reducer.py
        rm $HEC2/intermediate.msgpack.zst
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

def main():
    try:       
        with open("$HEC2/intermediate.msgpack.zst", "rb") as f:
            compressed = f.read()

        grouped = msgpack.unpackb(zstd.ZstdDecompressor().decompress(compressed))
        
        recommendations: ReducedData = reducer(grouped, N=10)
        
        with open("$HEC2/recommendations.txt", "w") as f:
            for user, recs in recommendations.items():
                recs_str = ",".join([f"{friend}" for friend in recs])
                f.write(f"{user}\\t{recs_str}\\n")

        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()

EOL

chmod +x $HEC2/reducer.sh

sudo yum install python-pip -y
pip install msgpack zstandard

nohup $HEC2/reducer.sh >> $HEC2/reducer.log 2>>$HEC2/reducer-error.log &

'''


PROJECT_NAME = "map-reduce-tp2"

DEFAULT_AMI_ID = "ami-0bdd88bd06d16ba03"