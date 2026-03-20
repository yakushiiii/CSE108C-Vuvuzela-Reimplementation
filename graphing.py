import pandas as pd
import glob
import matplotlib.pyplot as plt
import os


def compute_avg_latency(num_users):
    files = glob.glob(f"log_{num_users}_users/*.csv")
    df_list = []
    for f in files:
        df = pd.read_csv(f)

        df = df[df["round"].apply(lambda x: str(x).isdigit())]

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

# success vs missed vs late
def compute_status_rates(num_users):
    files = glob.glob(f"log_{num_users}_users/*.csv")

    counts = {"success": 0, "missed": 0, "late": 0}

    for f in files:
        df = pd.read_csv(f)

        if df.empty or "status" not in df.columns:
            continue

        # clean rows
        df = df[df["status"].isin(["success", "missed", "late"])]

        # count each status
        for status in counts:
            counts[status] += (df["status"] == status).sum()

    total = sum(counts.values())

    if total == 0:
        return 0, 0, 0

    return (
        counts["success"] / total,
        counts["missed"] / total,
        counts["late"] / total
    )

client_sizes = [50, 100, 200, 500]

success_rates = []
missed_rates = []
late_rates = []

for size in client_sizes:
    success, missed, late = compute_status_rates(size)
    success_rates.append(success)
    missed_rates.append(missed)
    late_rates.append(late)

plt.plot(client_sizes, success_rates, marker='o', label="Success")
plt.plot(client_sizes, missed_rates, marker='o', label="Missed")
plt.plot(client_sizes, late_rates, marker='o', label="Late")

plt.xlabel("Number of Users")
plt.ylabel("Rate")
plt.title("Message Delivery Reliability vs Number of Users")
plt.legend()
plt.show()

# latency histogram
def plot_latency_histogram(num_users):
    files = glob.glob(f"log_{num_users}_users/*.csv")
    df_list = []

    for f in files:
        df = pd.read_csv(f)

        if df.empty or "rtt" not in df.columns:
            continue

        df = df[df["status"] == "success"]
        df["rtt"] = pd.to_numeric(df["rtt"], errors="coerce")
        df = df.dropna(subset=["rtt"])

        df_list.append(df)

    combined = pd.concat(df_list, ignore_index=True)

    plt.hist(combined["rtt"], bins=20)
    plt.xlabel("RTT (seconds)")
    plt.ylabel("Number of Messages")
    plt.title(f"Latency Distribution ({num_users} Users)")
    plt.show()

for item in client_sizes:
    plot_latency_histogram(item)

