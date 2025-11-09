## Documentation:
# Purpose: EC2 user data script for automated WordCount performance benchmarking
# Execution: Runs automatically when Ubuntu EC2 instance launches
# 
# Complete Workflow:
# 1. System Setup:
#    - Updates Ubuntu package manager (apt-get update)
#    - Installs Java 11 JDK (required for Hadoop/Spark)
#    - Installs Python3, pip, wget, and analysis libraries (pandas, matplotlib)
#
# 2. Big Data Framework Installation:
#    - Downloads and installs Hadoop 3.4.2 from Apache mirrors
#    - Downloads and installs Spark 3.5.7 with Hadoop compatibility
#    - Configures environment variables (JAVA_HOME, HADOOP_HOME, SPARK_HOME, PATH)
#
# 3. Test Data Preparation:
#    - Creates directories for datasets (/home/ubuntu/datasets) and results (/home/ubuntu/results)
#    - Downloads 9 assignment-required text datasets from provided URLs
#    - Sets up CSV file for timing results with proper headers
#
# 4. Benchmarking Functions:
#    - run_linux_wc(): Tests native Linux commands (cat | tr | sort | uniq -c)
#    - run_hadoop_wc(): Tests Hadoop MapReduce using built-in WordCount example
#    - run_spark_wc(): Tests Spark using built-in Python WordCount example
#    - Each function runs 3 times per dataset for statistical reliability
#
# 5. Automated Execution:
#    - Processes all 9 datasets with all 3 frameworks
#    - Records execution times with nanosecond precision
#    - Saves results to CSV file for analysis
#
# 6. Results Analysis & Visualization:
#    - Calculate average execution times
#    - Generates comparison charts (Hadoop vs Linux, Hadoop vs Spark)
#    - Saves PNG charts to results directory
#
# Output Files:
# - /home/ubuntu/results/timings.csv (raw timing data)
# - /home/ubuntu/results/comparison_hadoop_linux.png (performance chart)
# - /home/ubuntu/results/comparison_hadoop_spark.png (performance chart)
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

run_linux_wc() {
    local file=$1
    local dataset_name=$(basename "$file")

    for run in {1..3}; do
        START=$(date +%s.%N)
        cat "$file" | tr ' ' '\n' | sort | uniq -c > /dev/null
        END=$(date +%s.%N)
        ELAPSED=$(echo "$END - $START" | bc)
        printf "%s,Linux,%d,%.4f\n" "$dataset_name" "$run" "$ELAPSED" >> "$RESULT_FILE"
    done
}

run_hadoop_wc() {
    local file=$1
    local dataset_name=$(basename $file)
    for run in {1..3}; do
        START=$(date +%s.%N)
        $HADOOP_HOME/bin/hadoop jar \
            $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-$HADOOP_VERSION.jar \
            wordcount file://$file file:///tmp/output >/dev/null 2>&1
        END=$(date +%s.%N)
        ELAPSED=$(echo "$END - $START" | bc)
        printf "%s,Hadoop,%d,%.4f\n" "$dataset_name" "$run" "$ELAPSED" >> "$RESULT_FILE"
        rm -rf /tmp/output
    done
}

run_spark_wc() {
    local file=$1
    local dataset_name=$(basename "$file")
    for run in {1..3}; do
        START=$(date +%s.%N)
        $SPARK_HOME/bin/spark-submit --master local[*] \
            $SPARK_HOME/examples/src/main/python/wordcount.py "$file" >/dev/null 2>&1
        END=$(date +%s.%N)
        ELAPSED=$(echo "$END - $START" | bc)
        printf "%s,Spark,%d,%.4f\n" "$dataset_name" "$run" "$ELAPSED" >> "$RESULT_FILE"
    done
}

for file in $DATA_DIR/*; do
    run_hadoop_wc $file
    run_linux_wc $file
    run_spark_wc $file
done

python3 <<EOF
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("$RESULT_FILE")

avg_df = df.groupby(['dataset','framework']).time_seconds.mean().reset_index()

subset1 = avg_df[avg_df['framework'].isin(['Hadoop', 'Linux'])]
pivot1 = subset1.pivot(index='dataset', columns='framework', values='time_seconds')

fig, ax = plt.subplots(figsize=(12,6))
pivot1.plot(kind='bar', ax=ax)
ax.set_ylabel("Average Execution Time (s)")
ax.set_title("Hadoop vs Linux WordCount")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig("$RESULT_DIR/comparison_hadoop_linux.png")
plt.close(fig)

subset2 = avg_df[avg_df['framework'].isin(['Hadoop', 'Spark'])]
pivot2 = subset2.pivot(index='dataset', columns='framework', values='time_seconds')

fig, ax = plt.subplots(figsize=(12,6))
pivot2.plot(kind='bar', ax=ax)
ax.set_ylabel("Average Execution Time (s)")
ax.set_title("Hadoop vs Spark WordCount")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig("$RESULT_DIR/comparison_hadoop_spark.png")
plt.close(fig)
EOF

echo "All experiments completed. Results saved in $RESULT_FILE, comparison_hadoop_linux.png, and comparison_hadoop_spark.png."
'''

UBUNTU_AMI_ID = "ami-0bbdd8c17ed981ef9" # Image containing Ubuntu OS, Python3, AWS CLI tools, apt-get as package manager, ...

WORD_COUNT_PROJECT_NAME = "WORDCOUNT-TP2"
