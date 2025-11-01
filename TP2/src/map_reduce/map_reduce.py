from collections import defaultdict

def mapper(data):
    """Simulates the Map step."""
    mapped = []

    for user, friends in data.items():
        # Emit direct friendships
        for f in friends:
            mapped.append((user, ("DIRECT", f)))
            mapped.append((f, ("DIRECT", user)))

        # Emit friends-of-friends (candidate recommendations)
        for f in friends:
            fof_list = [x for x in friends if x != f]
            if fof_list:
                mapped.append((f, ("FOF", fof_list)))

    return mapped


def shuffle(mapped):
    """Simulates the shuffle & sort step."""
    grouped = defaultdict(list)
    for key, value in mapped:
        grouped[key].append(value)
    return grouped


def reducer(grouped, N=10):
    """Simulates the Reduce step."""
    results = {}

    for user, values in grouped.items():
        direct = set()
        fof_lists = []

        for vtype, value in values:
            if vtype == "DIRECT":
                direct.add(value)
            elif vtype == "FOF":
                fof_lists.append(value)

        # Count mutual friends
        mutual_counts = defaultdict(int)
        for fof_group in fof_lists:
            for candidate in fof_group:
                if candidate != user and candidate not in direct:
                    mutual_counts[candidate] += 1

        # Take top N recommendations
        topN = sorted(mutual_counts.items(), key=lambda x: -x[1])[:N]

        results[user] = topN

    return results

def main():
    try:       
        data = {}

        with open("friendList.txt", "r") as f:
            for line in f:
                line = line.strip()
                
                if not line:
                    continue
                
                parts = line.split()
                
                if len(parts) == 1:
                    user = parts[0]
                    data[user] = []
                    continue
                
                if len(parts) != 2:
                    print("BAD LINE:", repr(line))
                    continue

                user, friends_str = parts
                friends_list = friends_str.split(",")

                data[user] = friends_list
           
        
        mapped = mapper(data)
        grouped = shuffle(mapped)
        recommendations = reducer(grouped, N=10)
        
        # Example output for user "0"
        print(recommendations["0"])
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
