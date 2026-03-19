import pandas as pd
import glob
import matplotlib as plt
import os


def compute_avg_latency(num_users):
    files = glob.glob(f"log_{num_users}_users/*.csv")
    df_list = []
    for f in files:
        df = pd.read_csv(f)
        df = df[df["round"].apply(lambda x: str(x).isdigit())]
        print(f"FILE: {f}")
        print(df.columns.tolist())
        print(df.head())
        df["rtt"] = pd.to_numeric(df["rtt"], errors="coerce")
        df_list.append(df)

    combined = pd.concat(df_list, ignore_index=True)
    return combined["rtt"].mean()

client_sizes = [50, 100, 200, 500]
avg_latencies = []

for item in client_sizes:
    avg = compute_avg_latency(item)
    avg_latencies.append(avg)

#graph comparing average round trip time of messages based on the number of users
plt.plot(client_sizes, avg_latencies, marker='o')
plt.xlabel("Number of Clients")
plt.ylabel("Average Round Trip Time (seconds)")
plt.title("Latency vs Number of Clients")
plt.grid(True)
plt.show()