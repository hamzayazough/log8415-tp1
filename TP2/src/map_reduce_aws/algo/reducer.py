from collections import defaultdict
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
        INSTANCE_NUMBER = 1
        for i in range(1, INSTANCE_NUMBER + 1):
            with open(f"intermediate-{i}.msgpack.zst", "rb") as f:
                compressed = f.read()
                grouped = msgpack.unpackb(zstd.ZstdDecompressor().decompress(compressed))
                groups.append(grouped)
                
        grouped = merge_dicts(*groups)

        recommendations: ReducedData = reducer(grouped, N=10)
        
        with open("recommendations.txt", "w") as f:
            for user, recs in recommendations.items():
                recs_str = ",".join([f"{friend}" for friend in recs])
                f.write(f"{user}\t{recs_str}\n")

        selected_ids = ["924", "8941", "8942", "9019", "9020", "9021", "9022", "9990", "9992", "9993"]
        with open("selected_recommendations.txt", "w") as f:
            for user in selected_ids:
                recs = recommendations.get(user)
                if recs:
                    recs_str = ",".join([f"{friend}" for friend in recs])
                    f.write(f"{user}\t{recs_str}\n")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
