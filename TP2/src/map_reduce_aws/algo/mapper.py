from collections import defaultdict
import json

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

        with open("friendList.txt", "r") as f:
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
        
        with open("intermediate.json", "w") as f:
            json.dump(grouped, f)
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
