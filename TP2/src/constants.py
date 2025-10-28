USER_DATA_SCRIPT_WORDCOUNT = '''#!/bin/bash
set -e

apt-get update -y
apt-get install -y openjdk-11-jdk python3 python3-pip wget

pip3 install pandas matplotlib

export JAVA_HOME=$(readlink -f /usr/bin/java | sed "s:bin/java::")
export HADOOP_VERSION=3.4.2
export SPARK_VERSION=3.5.7
export HADOOP_HOME=/home/ubuntu/hadoop
export SPARK_HOME=/home/ubuntu/spark
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin

wget https://dlcdn.apache.org/hadoop/common/hadoop-$HADOOP_VERSION/hadoop-$HADOOP_VERSION.tar.gz -P /tmp
tar -xzf /tmp/hadoop-$HADOOP_VERSION.tar.gz -C /home/ubuntu
mv /home/ubuntu/hadoop-$HADOOP_VERSION $HADOOP_HOME

cat > $HADOOP_HOME/etc/hadoop/hadoop-env.sh <<EOL
export JAVA_HOME=$JAVA_HOME
EOL

wget https://dlcdn.apache.org/spark/spark-$SPARK_VERSION/spark-$SPARK_VERSION-bin-hadoop3.tgz -P /tmp
tar -xzf /tmp/spark-$SPARK_VERSION-bin-hadoop3.tgz -C /home/ubuntu
mv /home/ubuntu/spark-$SPARK_VERSION-bin-hadoop3 $SPARK_HOME

DATA_DIR=/home/ubuntu/datasets
RESULT_DIR=/home/ubuntu/results
mkdir -p $DATA_DIR $RESULT_DIR

DATASETS=(
    "https://tinyurl.com/4vxdw3pa"
    "https://tinyurl.com/kh9excea"
    "https://tinyurl.com/dybs9bnk"
    "https://tinyurl.com/datumz6m"
    "https://tinyurl.com/j4j4xdw6"
    "https://tinyurl.com/ym8s5fm4"
    "https://tinyurl.com/2h6a75nk"
    "https://tinyurl.com/vwvram8"
    "https://tinyurl.com/weh83uyn"
)

for url in "${DATASETS[@]}"; do
    wget -O "$DATA_DIR/$(basename $url).txt" "$url"
done

RESULT_FILE=$RESULT_DIR/timings.csv
echo "dataset,framework,run,time_seconds" > $RESULT_FILE

run_hadoop_wc() {
    local file=$1
    local dataset_name=$(basename $file)
    for run in {1..3}; do
        START=$(date +%s)
        $HADOOP_HOME/bin/hadoop jar \
            $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-$HADOOP_VERSION.jar \
            wordcount file://$file file:///tmp/output >/dev/null 2>&1
        END=$(date +%s)
        ELAPSED=$((END-START))
        echo "$dataset_name,Hadoop,$run,$ELAPSED" >> $RESULT_FILE
        rm -rf /tmp/output
    done
}

run_spark_wc() {
    local file=$1
    local dataset_name=$(basename "$file")
    for run in {1..3}; do
        START=$(date +%s)
        $SPARK_HOME/bin/spark-submit --master local[*] \
            $SPARK_HOME/examples/src/main/python/wordcount.py "$file" >/dev/null 2>&1
        END=$(date +%s)
        ELAPSED=$((END - START))
        echo "$dataset_name,Spark,$run,$ELAPSED" >> "$RESULT_FILE"
    done
}

for file in $DATA_DIR/*; do
    run_hadoop_wc $file
    run_spark_wc $file
done

python3 <<EOF
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("$RESULT_FILE")

avg_df = df.groupby(['dataset','framework']).time_seconds.mean().reset_index()
avg_df_pivot = avg_df.pivot(index='dataset', columns='framework', values='time_seconds')

fig, ax = plt.subplots(figsize=(12,6))
avg_df_pivot.plot(kind='bar', ax=ax)
ax.set_ylabel("Average Execution Time (s)")
ax.set_title("Hadoop vs Spark WordCount")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig("$RESULT_DIR/comparison_plot.png")
EOF

echo "All experiments completed. Results saved in $RESULT_FILE and comparison_plot.png"
'''

USER_DATA_SCRIPT = '''#!/bin/bash
yum update -y
yum install -y python3 python3-pip
pip3 install fastapi uvicorn

mkdir -p /home/ec2-user/app
cd /home/ec2-user/app

cat > main.py << 'EOF'
from fastapi import FastAPI
import subprocess

app = FastAPI()

def get_instance_id():
    try:
        result = subprocess.run(['curl', '-s', 'http://169.254.169.254/latest/meta-data/instance-id'], 
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else 'unknown'
    except:
        return 'unknown'

@app.get("/")
async def root():
    instance_id = get_instance_id()
    return {{"message": f"Instance {{instance_id}} is responding now!", "instance_id": instance_id, "cluster": "{cluster_name}"}}

@app.get("/health")
async def health():
    return {{"status": "healthy", "instance_id": get_instance_id(), "cluster": "{cluster_name}"}}

@app.get("/cluster1")
async def cluster1():
    instance_id = get_instance_id()
    return {{"message": f"Cluster1 - Instance {{instance_id}} is responding now!", "instance_id": instance_id, "cluster": "cluster1"}}

@app.get("/cluster2")
async def cluster2():
    instance_id = get_instance_id()
    return {{"message": f"Cluster2 - Instance {{instance_id}} is responding now!", "instance_id": instance_id, "cluster": "cluster2"}}
EOF

chown -R ec2-user:ec2-user /home/ec2-user/app
cd /home/ec2-user/app
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
'''

PROJECT_NAME = 'LOG8415E-TP1'
DEFAULT_AMI_ID = "ami-0c02fb55956c7d316"

CLUSTER_CONFIGS = {
    'cluster1': {
        'instance_type': 't2.large',
        'count': 4,
        'name': 'Cluster1'
    },
    'cluster2': {
        'instance_type': 't2.micro',
        'count': 4,
        'name': 'Cluster2'
    }
}