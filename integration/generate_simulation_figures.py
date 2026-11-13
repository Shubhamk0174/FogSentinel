import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

os.environ["MPLCONFIGDIR"] = str(Path(".cache/matplotlib").resolve())
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def generate_simulation_figures(csv_path="outputs/simulation/simulation_results.csv",
                                output_dir="outputs/figures"):
    """
    Generates all faculty-ready visualization figures directly from raw simulation CSV results.
    Never invents or hardcodes data.
    """
    if not os.path.exists(csv_path):
        # Fall back to quick demo results if full sweep hasn't been run yet
        quick_csv = "outputs/simulation/quick_demo_results.csv"
        if os.path.exists(quick_csv):
            csv_path = quick_csv
        else:
            raise FileNotFoundError(f"Neither {csv_path} nor {quick_csv} found.")
            
    df = pd.read_csv(csv_path)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    print(f"[Analysis] Generating simulation charts from: {csv_path} ({len(df)} records)")
    
    # 1. Fog vs Cloud Latency Chart (Filtered by 10 devices, rate 1.0)
    df_10 = df[(df["device_count"] == 10) & (df["record_rate_per_sec"] == 1.0)]
    if not df_10.empty:
        plt.figure(figsize=(9, 5))
        wan_lats = sorted(df_10["wan_latency_ms"].unique())
        
        fog_vals = [df_10[(df_10["wan_latency_ms"] == lat) & (df_10["placement"] == "fog")]["mean_latency_ms"].values[0]
                    if len(df_10[(df_10["wan_latency_ms"] == lat) & (df_10["placement"] == "fog")]) > 0 else 0
                    for lat in wan_lats]
                    
        cloud_vals = [df_10[(df_10["wan_latency_ms"] == lat) & (df_10["placement"] == "cloud")]["mean_latency_ms"].values[0]
                      if len(df_10[(df_10["wan_latency_ms"] == lat) & (df_10["placement"] == "cloud")]) > 0 else 0
                      for lat in wan_lats]
                      
        x = np.arange(len(wan_lats))
        width = 0.35
        
        plt.bar(x - width/2, fog_vals, width, label="Fog Placement", color="#2ca02c", edgecolor="black")
        plt.bar(x + width/2, cloud_vals, width, label="Cloud Placement", color="#1f77b4", edgecolor="black")
        
        plt.xlabel("Configured One-Way WAN Latency (ms)", fontsize=11)
        plt.ylabel("Mean End-to-End Latency (ms)", fontsize=11)
        plt.title("Fog vs. Cloud Mean Response Latency Across WAN Link Delays\n(10 IoT Devices | 1.0 record/sec)", fontsize=12, pad=12)
        plt.xticks(x, [f"{int(l)} ms" for l in wan_lats])
        plt.legend(frameon=True)
        plt.grid(axis="y", linestyle="--", alpha=0.6)
        plt.tight_layout()
        f1_path = out_path / "fog_vs_cloud_latency.png"
        plt.savefig(f1_path, dpi=300)
        plt.close()
        print(f"  Saved: {f1_path}")
        
    # 2. Latency vs Device Count (Scalability)
    if len(df["device_count"].unique()) > 1:
        plt.figure(figsize=(9, 5))
        dev_counts = sorted(df["device_count"].unique())
        
        # Pick 100 ms WAN latency and 1.0 rate as standard baseline
        df_scale = df[(df["wan_latency_ms"] == 100.0) & (df["record_rate_per_sec"] == 1.0)]
        if not df_scale.empty:
            fog_lat = [df_scale[(df_scale["device_count"] == d) & (df_scale["placement"] == "fog")]["mean_latency_ms"].values[0]
                       if len(df_scale[(df_scale["device_count"] == d) & (df_scale["placement"] == "fog")]) > 0 else None
                       for d in dev_counts]
            cloud_lat = [df_scale[(df_scale["device_count"] == d) & (df_scale["placement"] == "cloud")]["mean_latency_ms"].values[0]
                         if len(df_scale[(df_scale["device_count"] == d) & (df_scale["placement"] == "cloud")]) > 0 else None
                         for d in dev_counts]
                         
            plt.plot(dev_counts, fog_lat, marker="o", linewidth=2.5, color="#2ca02c", label="Fog Placement")
            plt.plot(dev_counts, cloud_lat, marker="s", linewidth=2.5, color="#1f77b4", label="Cloud Placement")
            
            plt.xlabel("Number of Connected IoT Devices", fontsize=11)
            plt.ylabel("Mean End-to-End Latency (ms)", fontsize=11)
            plt.title("Scalability: Latency vs. Device Count (WAN Latency = 100 ms)", fontsize=12, pad=12)
            plt.xticks(dev_counts)
            plt.legend(frameon=True)
            plt.grid(True, linestyle="--", alpha=0.6)
            plt.tight_layout()
            f2_path = out_path / "latency_vs_device_count.png"
            plt.savefig(f2_path, dpi=300)
            plt.close()
            print(f"  Saved: {f2_path}")

    # 3. WAN Traffic Comparison (KB)
    plt.figure(figsize=(8, 5))
    placements = ["fog", "cloud"]
    wan_bytes = [
        df[df["placement"] == "fog"]["wan_bytes_transmitted"].mean() / 1024.0,
        df[df["placement"] == "cloud"]["wan_bytes_transmitted"].mean() / 1024.0
    ]
    plt.bar(["Fog Placement", "Cloud Placement"], wan_bytes, color=["#2ca02c", "#d62728"], edgecolor="black", width=0.45)
    plt.ylabel("WAN Bandwidth Consumption (KB)", fontsize=11)
    plt.title("Average WAN Traffic Overhead: Fog vs. Cloud Processing", fontsize=12, pad=12)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    for i, v in enumerate(wan_bytes):
        plt.text(i, v + (max(wan_bytes)*0.02), f"{v:,.1f} KB", ha="center", fontweight="bold", fontsize=10)
    plt.tight_layout()
    f3_path = out_path / "wan_traffic_comparison.png"
    plt.savefig(f3_path, dpi=300)
    plt.close()
    print(f"  Saved: {f3_path}")

    # 4. Energy Model Comparison
    plt.figure(figsize=(9, 5))
    avg_cloud_energy = [
        df[df["placement"] == "fog"]["cloud_energy_joules"].mean() / 1000.0,
        df[df["placement"] == "cloud"]["cloud_energy_joules"].mean() / 1000.0
    ]
    avg_fog_energy = [
        df[df["placement"] == "fog"]["fog_energy_joules"].mean() / 1000.0,
        df[df["placement"] == "cloud"]["fog_energy_joules"].mean() / 1000.0
    ]
    x = np.arange(2)
    w = 0.35
    plt.bar(x - w/2, avg_fog_energy, w, label="Fog Gateway Energy (kJ)", color="#ff7f0e", edgecolor="black")
    plt.bar(x + w/2, avg_cloud_energy, w, label="Cloud Server Energy (kJ)", color="#9467bd", edgecolor="black")
    plt.xticks(x, ["Fog Placement", "Cloud Placement"])
    plt.ylabel("Energy Consumption (Kilojoules)", fontsize=11)
    plt.title("Modelled Energy Consumption (Linear Power Model)", fontsize=12, pad=12)
    plt.legend(frameon=True)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    f4_path = out_path / "energy_comparison.png"
    plt.savefig(f4_path, dpi=300)
    plt.close()
    print(f"  Saved: {f4_path}")

    print("[Analysis] All figures generated successfully.")

if __name__ == "__main__":
    generate_simulation_figures()

