import pytest
import pandas as pd
from pathlib import Path

def test_quick_demo_results():
    csv_path = Path("outputs/simulation/quick_demo_results.csv")
    assert csv_path.exists(), "quick_demo_results.csv must exist"
    df = pd.read_csv(csv_path)

    assert len(df) == 2, f"Quick demo must have 2 records (fog and cloud), got {len(df)}"
    placements = set(df["placement"].str.lower())
    assert placements == {"fog", "cloud"}, f"Expected fog and cloud placements, got {placements}"

    fog_row = df[df["placement"].str.lower() == "fog"].iloc[0]
    cloud_row = df[df["placement"].str.lower() == "cloud"].iloc[0]

    # Fog latency must be strictly lower than Cloud latency
    assert fog_row["mean_latency_ms"] < cloud_row["mean_latency_ms"], \
        f"Fog latency ({fog_row['mean_latency_ms']:.2f}ms) must be lower than cloud ({cloud_row['mean_latency_ms']:.2f}ms)"

    # Fog WAN bytes must be 0
    assert fog_row["wan_bytes_transmitted"] == 0, \
        f"Fog placement WAN bytes must be 0, got {fog_row['wan_bytes_transmitted']}"

    # Cloud WAN bytes must be positive
    assert cloud_row["wan_bytes_transmitted"] > 0, \
        f"Cloud placement WAN bytes must be positive, got {cloud_row['wan_bytes_transmitted']}"

    # Both completed counts must be positive and non-zero
    assert fog_row["completed_count"] > 0, "Fog completed count must be > 0"
    assert cloud_row["completed_count"] > 0, "Cloud completed count must be > 0"

def test_full_sweep_results():
    csv_path = Path("outputs/simulation/simulation_results.csv")
    assert csv_path.exists(), "simulation_results.csv must exist"
    df = pd.read_csv(csv_path)

    # 48 scenarios total
    assert len(df) == 48, f"Expected 48 sweep records, got {len(df)}"

    # Required columns
    expected_cols = [
        "device_count", "record_rate_per_sec", "wan_latency_ms", "placement",
        "sim_time_sec", "generated_count", "completed_count", "dropped_count",
        "mean_latency_ms", "median_latency_ms", "p95_latency_ms",
        "wan_bytes_transmitted", "cloud_energy_joules", "fog_energy_joules"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column {col} in sweep results"

    # Fog WAN bytes must always be 0
    fog_records = df[df["placement"].str.lower() == "fog"]
    assert (fog_records["wan_bytes_transmitted"] == 0).all(), "All fog placements must have 0 WAN bytes"

    # Cloud WAN bytes must always be > 0
    cloud_records = df[df["placement"].str.lower() == "cloud"]
    assert (cloud_records["wan_bytes_transmitted"] > 0).all(), "All cloud placements must have positive WAN bytes"

    # Completed counts must be positive across all scenarios
    assert (df["completed_count"] > 0).all(), "Completed counts must be > 0 in all scenarios"

def test_html_dashboard_artifact():
    html_path = Path("dashboard/index.html")
    assert html_path.exists(), "dashboard/index.html must exist"
    content = html_path.read_text(encoding="utf-8")
    assert len(content) > 50000, "dashboard/index.html must not be empty"
    assert "SIM_DATA" in content, "dashboard/index.html must contain embedded simulation sweep data"
    assert "DEMO_DATA" in content, "dashboard/index.html must contain embedded demo data"
    assert "topology-svg" in content, "dashboard/index.html must contain SVG topology visualizer"

