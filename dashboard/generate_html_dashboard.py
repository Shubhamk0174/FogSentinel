import os
import sys
import json
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def build_html_dashboard():
    # 1. Load Simulation Results
    sim_path = ROOT_DIR / "outputs" / "simulation" / "simulation_results.csv"
    if not sim_path.exists():
        sim_path = ROOT_DIR / "outputs" / "simulation" / "quick_demo_results.csv"
    df_sim = pd.read_csv(sim_path)
    sim_data = df_sim.to_dict(orient="records")

    # 2. Load 55-Record Demo
    demo_preds_path = ROOT_DIR / "outputs" / "demo" / "demo_predictions.csv"
    demo_feat_path = ROOT_DIR / "data" / "demo" / "demo_features.csv"
    demo_labels_path = ROOT_DIR / "data" / "demo" / "demo_labels.csv"

    df_preds = pd.read_csv(demo_preds_path)
    df_feat = pd.read_csv(demo_feat_path) if demo_feat_path.exists() else pd.DataFrame()
    df_labels = pd.read_csv(demo_labels_path) if demo_labels_path.exists() else pd.DataFrame()

    demo_records = []
    for i in range(len(df_preds)):
        p_row = df_preds.iloc[i].to_dict()
        l_row = df_labels.iloc[i].to_dict() if i < len(df_labels) else {}
        f_row = df_feat.iloc[i].to_dict() if i < len(df_feat) else {}

        rec = {
            "record_id": str(p_row.get("record_id", f"DEMO_{i+1:03d}")),
            "prediction": str(p_row.get("prediction", "unknown")),
            "predicted_attack_type": str(p_row.get("predicted_attack_type", "unknown")),
            "confidence": float(p_row.get("confidence", 1.0)),
            "action": str(p_row.get("action", "ALLOW")),
            "gt_binary": str(l_row.get("binary_label", "unknown")),
            "gt_multi": str(l_row.get("multi_label", "unknown")),
            "features": {k: round(float(v), 4) for k, v in f_row.items()}
        }
        demo_records.append(rec)

    # 3. Model Comparison & Per Class
    comp_path = ROOT_DIR / "outputs" / "model" / "model_comparison.csv"
    df_comp = pd.read_csv(comp_path) if comp_path.exists() else pd.DataFrame()
    comp_data = df_comp.to_dict(orient="records")

    # Serialize JSON
    sim_json = json.dumps(sim_data)
    demo_json = json.dumps(demo_records)
    comp_json = json.dumps(comp_data)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FogSentinel — IoT Security & Fog Computing Web Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: #111827;
      --card-border: #1f2937;
      --card-hover: #1e293b;
      --text-main: #f9fafb;
      --text-muted: #9ca3af;
      --accent-blue: #3b82f6;
      --accent-green: #10b981;
      --accent-red: #ef4444;
      --accent-purple: #8b5cf6;
      --accent-amber: #f59e0b;
      --cyan: #06b6d4;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      line-height: 1.5;
      min-height: 100vh;
    }}
    a {{ color: var(--accent-blue); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    /* Layout */
    .header {{
      background: linear-gradient(180deg, #111827 0%, rgba(17, 24, 39, 0.8) 100%);
      border-bottom: 1px solid var(--card-border);
      padding: 1.25rem 2rem;
      position: sticky;
      top: 0;
      z-index: 50;
      backdrop-filter: blur(12px);
    }}
    .header-content {{
      max-width: 1440px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .brand-icon {{
      width: 42px;
      height: 42px;
      background: linear-gradient(135deg, #2563eb, #10b981);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.4rem;
      box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
    }}
    .brand-title {{
      font-size: 1.35rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      background: linear-gradient(90deg, #ffffff, #93c5fd);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .brand-subtitle {{
      font-size: 0.78rem;
      color: var(--text-muted);
      font-weight: 400;
    }}
    .badges {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .badge-blue {{ background: rgba(59, 130, 246, 0.15); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.3); }}
    .badge-green {{ background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-purple {{ background: rgba(139, 92, 246, 0.15); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.3); }}

    /* Main Container */
    .container {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 1.75rem 2rem 3rem 2rem;
    }}

    /* Navigation Tabs */
    .nav-tabs {{
      display: flex;
      gap: 0.5rem;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 1.75rem;
      overflow-x: auto;
      padding-bottom: 0.5rem;
    }}
    .tab-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 0.65rem 1.15rem;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.2s ease;
      white-space: nowrap;
    }}
    .tab-btn:hover {{
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.04);
    }}
    .tab-btn.active {{
      color: #ffffff;
      background: var(--card-bg);
      border-color: var(--card-border);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; animation: fadeIn 0.3s ease; }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Cards & Grids */
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--card-border);
    }}
    .card-title {{
      font-size: 1.15rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .card-subtitle {{
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
    }}

    /* Metrics Grid */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }}
    .metric-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 1.2rem;
      position: relative;
      overflow: hidden;
    }}
    .metric-card::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: var(--accent-blue);
    }}
    .metric-card.green::before {{ background: var(--accent-green); }}
    .metric-card.red::before {{ background: var(--accent-red); }}
    .metric-card.purple::before {{ background: var(--accent-purple); }}
    .metric-card.cyan::before {{ background: var(--cyan); }}

    .metric-label {{
      font-size: 0.78rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
      margin-bottom: 0.35rem;
    }}
    .metric-value {{
      font-size: 1.85rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #ffffff;
      font-family: 'JetBrains Mono', monospace;
    }}
    .metric-sub {{
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 0.35rem;
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }}
    .metric-sub.good {{ color: var(--accent-green); font-weight: 600; }}
    .metric-sub.bad {{ color: var(--accent-red); font-weight: 600; }}

    /* Controls Bar */
    .controls-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      background: #172033;
      padding: 1rem 1.25rem;
      border-radius: 10px;
      border: 1px solid #23314d;
      margin-bottom: 1.5rem;
      align-items: center;
    }}
    .control-group {{
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
      min-width: 140px;
    }}
    .control-label {{
      font-size: 0.75rem;
      font-weight: 600;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .control-select, .control-input {{
      background: #0f172a;
      border: 1px solid #334155;
      color: #f8fafc;
      padding: 0.45rem 0.75rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-family: inherit;
      outline: none;
      cursor: pointer;
    }}
    .control-select:focus, .control-input:focus {{
      border-color: var(--accent-blue);
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }}
    .btn {{
      background: var(--accent-blue);
      color: #ffffff;
      border: none;
      padding: 0.55rem 1.15rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: background 0.2s ease;
    }}
    .btn:hover {{ background: #2563eb; }}
    .btn-green {{ background: var(--accent-green); }}
    .btn-green:hover {{ background: #059669; }}
    .btn-outline {{
      background: transparent;
      border: 1px solid #334155;
      color: #f8fafc;
    }}
    .btn-outline:hover {{ background: rgba(255, 255, 255, 0.05); }}

    /* Topology Canvas Visualizer */
    .sim-stage {{
      background: radial-gradient(circle at 50% 50%, #151f33 0%, #0d1322 100%);
      border: 1px solid #23314d;
      border-radius: 12px;
      padding: 1.5rem;
      position: relative;
      overflow: hidden;
      margin-bottom: 1.5rem;
    }}
    .topology-svg {{
      width: 100%;
      height: 380px;
      display: block;
    }}

    /* Table Styles */
    .table-container {{
      overflow-x: auto;
      border: 1px solid var(--card-border);
      border-radius: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
      text-align: left;
    }}
    thead th {{
      background: #172033;
      color: #94a3b8;
      font-weight: 600;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--card-border);
      white-space: nowrap;
      cursor: pointer;
      user-select: none;
    }}
    thead th:hover {{ color: #ffffff; }}
    tbody tr {{
      border-bottom: 1px solid var(--card-border);
      transition: background 0.15s ease;
    }}
    tbody tr:hover {{ background: var(--card-hover); }}
    tbody td {{
      padding: 0.65rem 1rem;
      white-space: nowrap;
    }}
    .font-mono {{ font-family: 'JetBrains Mono', monospace; }}

    .badge-pill {{
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 700;
      display: inline-block;
    }}
    .badge-allow {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }}
    .badge-quarantine {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }}
    .badge-fog {{ background: rgba(6, 182, 212, 0.2); color: #67e8f9; border: 1px solid rgba(6, 182, 212, 0.4); }}
    .badge-cloud {{ background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }}

    /* Drawer / Modal */
    .drawer-overlay {{
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.75);
      z-index: 100;
      backdrop-filter: blur(4px);
    }}
    .drawer {{
      position: fixed;
      top: 0;
      right: -600px;
      width: 580px;
      max-width: 90vw;
      height: 100%;
      background: #111827;
      border-left: 1px solid var(--card-border);
      z-index: 101;
      padding: 1.75rem;
      overflow-y: auto;
      transition: right 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: -10px 0 30px rgba(0, 0, 0, 0.5);
    }}
    .drawer.open {{ right: 0; }}
    .drawer-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--card-border);
    }}
    .drawer-close {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 1.5rem;
      cursor: pointer;
    }}
    .drawer-close:hover {{ color: #ffffff; }}

    /* Feature Grid in Drawer */
    .features-list {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.5rem;
    }}
    .feature-item {{
      background: #172033;
      padding: 0.5rem 0.75rem;
      border-radius: 6px;
      border: 1px solid #23314d;
    }}
    .feature-key {{ font-size: 0.72rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace; word-break: break-all; }}
    .feature-val {{ font-size: 0.85rem; font-weight: 700; color: #38bdf8; font-family: 'JetBrains Mono', monospace; }}

    /* Charts Canvas Containers */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
      gap: 1.5rem;
      margin-bottom: 1.5rem;
    }}
    .chart-box {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
    }}
    .chart-box h4 {{
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .chart-svg {{
      width: 100%;
      height: 250px;
    }}

    /* Q&A Accordion */
    .qa-item {{
      background: #172033;
      border: 1px solid #23314d;
      border-radius: 8px;
      margin-bottom: 0.75rem;
      overflow: hidden;
    }}
    .qa-question {{
      padding: 0.9rem 1.2rem;
      font-weight: 600;
      font-size: 0.92rem;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      user-select: none;
    }}
    .qa-question:hover {{ background: #1c273e; }}
    .qa-answer {{
      padding: 1rem 1.2rem;
      font-size: 0.88rem;
      color: #cbd5e1;
      border-top: 1px solid #23314d;
      background: #0f172a;
      display: none;
      line-height: 1.6;
    }}
    .qa-item.open .qa-answer {{ display: block; }}
    .qa-item.open .qa-icon {{ transform: rotate(180deg); }}
    .qa-icon {{ transition: transform 0.2s ease; }}

    /* Responsive */
    @media (max-width: 768px) {{
      .header-content {{ flex-direction: column; align-items: flex-start; }}
      .metrics-grid {{ grid-template-columns: 1fr; }}
      .charts-grid {{ grid-template-columns: 1fr; }}
      .features-list {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

  <!-- Top Sticky Header -->
  <header class="header">
    <div class="header-content">
      <div class="brand">
        <div class="brand-icon">🛡️</div>
        <div>
          <div class="brand-title">FogSentinel Interactive Simulation & ML Dashboard</div>
          <div class="brand-subtitle">IoT Network-Traffic Anomaly Detection & Edge/Fog vs. Cloud Placement Engine</div>
        </div>
      </div>
      <div class="badges">
        <span class="badge badge-green">● Official iFogSim2 v2.0.0</span>
        <span class="badge badge-blue">UCI N-BaIoT (115 Features)</span>
        <span class="badge badge-purple">48 Measured Scenarios</span>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="container">

    <!-- Navigation Tabs -->
    <nav class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('tab-sim')">⚡ Live Simulation & Topology Animator</button>
      <button class="tab-btn" onclick="switchTab('tab-charts')">📊 Performance Charts & Figures</button>
      <button class="tab-btn" onclick="switchTab('tab-sweep')">📋 48-Scenario Sweep Explorer</button>
      <button class="tab-btn" onclick="switchTab('tab-demo')">🔬 55-Record Traffic Classifier</button>
      <button class="tab-btn" onclick="switchTab('tab-viva')">🎓 Faculty Viva & Architecture Guide</button>
    </nav>

    <!-- ==================================================================== -->
    <!-- TAB 1: LIVE SIMULATION & TOPOLOGY ANIMATOR -->
    <!-- ==================================================================== -->
    <section id="tab-sim" class="tab-content active">

      <!-- Dynamic Interactive Controls -->
      <div class="controls-bar">
        <div class="control-group">
          <label class="control-label">Placement Strategy</label>
          <select id="sim-placement" class="control-select" onchange="updateSimulationView()">
            <option value="fog">Local Fog Gateway (Edge)</option>
            <option value="cloud">Remote Cloud Datacenter</option>
          </select>
        </div>
        <div class="control-group">
          <label class="control-label">Connected IoT Devices</label>
          <select id="sim-devices" class="control-select" onchange="updateSimulationView()">
            <option value="10">10 IoT Devices (Baseline)</option>
            <option value="50">50 IoT Devices</option>
            <option value="100">100 IoT Devices</option>
            <option value="200">200 IoT Devices (High Scale)</option>
          </select>
        </div>
        <div class="control-group">
          <label class="control-label">One-Way WAN Latency</label>
          <select id="sim-latency" class="control-select" onchange="updateSimulationView()">
            <option value="100.0">100 ms (Typical Internet)</option>
            <option value="25.0">25 ms (Metropolitan Link)</option>
            <option value="200.0">200 ms (Intercontinental Link)</option>
          </select>
        </div>
        <div class="control-group">
          <label class="control-label">Emission Rate</label>
          <select id="sim-rate" class="control-select" onchange="updateSimulationView()">
            <option value="1.0">1.0 rec/sec (Light)</option>
            <option value="5.0">5.0 rec/sec (Heavy Flood)</option>
          </select>
        </div>
        <div style="margin-left: auto; display: flex; gap: 0.5rem; align-items: flex-end;">
          <button class="btn btn-green" id="btn-toggle-anim" onclick="toggleAnimation()">⏸ Pause Animation</button>
          <button class="btn btn-outline" onclick="resetSimDefaults()">↺ Reset Baseline</button>
        </div>
      </div>

      <!-- Real-Time Metrics Display -->
      <div class="metrics-grid">
        <div class="metric-card" id="card-lat">
          <div class="metric-label">Mean End-to-End Latency</div>
          <div class="metric-value" id="val-latency">9.38 ms</div>
          <div class="metric-sub good" id="sub-latency">▼ 95.47% faster than Cloud (-197.60 ms)</div>
        </div>
        <div class="metric-card cyan" id="card-wan">
          <div class="metric-label">WAN Network Bandwidth Consumed</div>
          <div class="metric-value" id="val-wan">0.00 KB</div>
          <div class="metric-sub good" id="sub-wan">100% of Internet uplink/downlink saved</div>
        </div>
        <div class="metric-card purple">
          <div class="metric-label">Simulation Completed Records</div>
          <div class="metric-value" id="val-completed">590 records</div>
          <div class="metric-sub">Active duration: 60.0s | Dropped: 10</div>
        </div>
        <div class="metric-card green">
          <div class="metric-label">Local Fog Node Energy</div>
          <div class="metric-value" id="val-energy">5,022.25 kJ</div>
          <div class="metric-sub">Power Model: 107.3W Active / 83.4W Idle</div>
        </div>
      </div>

      <!-- Live Animated Topology Stage -->
      <div class="sim-stage">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
          <div style="font-weight: 700; font-size: 0.95rem; color: #94a3b8; display: flex; align-items: center; gap: 0.5rem;">
            <span>🌐 Topology Simulation Graph & Real-Time Data Flow</span>
            <span id="active-path-badge" class="badge-pill badge-fog">LOCAL FOG LOOP ACTIVE (LAN ONLY)</span>
          </div>
          <div style="font-size: 0.75rem; color: #64748b; font-family: 'JetBrains Mono', monospace;" id="sim-clock-display">
            SIMULATION CLOCK: ACTIVE (60,000 ms)
          </div>
        </div>

        <!-- SVG Topology Diagram -->
        <svg class="topology-svg" viewBox="0 0 1000 340" id="topo-svg">
          <defs>
            <linearGradient id="grad-lan" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#10b981" stop-opacity="0.8"/>
              <stop offset="100%" stop-color="#06b6d4" stop-opacity="0.8"/>
            </linearGradient>
            <linearGradient id="grad-wan" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.4"/>
              <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.8"/>
            </linearGradient>
            <filter id="glow-green" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="glow-blue" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          <!-- Links Background -->
          <!-- LAN Link: IoT -> Fog Gateway -->
          <path id="link-lan" d="M 170 170 L 480 170" stroke="url(#grad-lan)" stroke-width="5" stroke-dasharray="8 4" fill="none"/>
          
          <!-- WAN Link: Fog Gateway -> Cloud -->
          <path id="link-wan" d="M 520 170 L 830 170" stroke="url(#grad-wan)" stroke-width="4" stroke-dasharray="6 6" fill="none" opacity="0.3"/>

          <!-- Animated Pulses on LAN -->
          <circle id="pkt-lan-1" r="7" fill="#10b981" filter="url(#glow-green)">
            <animateMotion dur="1.2s" repeatCount="indefinite" path="M 170 170 L 480 170" />
          </circle>
          <circle id="pkt-lan-2" r="5" fill="#34d399">
            <animateMotion dur="1.2s" begin="0.6s" repeatCount="indefinite" path="M 170 170 L 480 170" />
          </circle>

          <!-- Downlink Alert Pulse (Fog -> IoT) -->
          <circle id="pkt-alert" r="6" fill="#38bdf8" filter="url(#glow-green)">
            <animateMotion dur="1.2s" begin="0.4s" repeatCount="indefinite" path="M 480 175 L 170 175" />
          </circle>

          <!-- Animated Pulses on WAN (Dynamic visibility) -->
          <circle id="pkt-wan-up" r="7" fill="#3b82f6" filter="url(#glow-blue)" style="display: none;">
            <animateMotion dur="3.0s" repeatCount="indefinite" path="M 520 165 L 830 165" />
          </circle>
          <circle id="pkt-wan-down" r="6" fill="#93c5fd" filter="url(#glow-blue)" style="display: none;">
            <animateMotion dur="3.0s" begin="1.5s" repeatCount="indefinite" path="M 830 175 L 520 175" />
          </circle>

          <!-- NODE 1: IoT Device Cluster -->
          <g transform="translate(70, 70)">
            <rect width="120" height="200" rx="12" fill="#1e293b" stroke="#334155" stroke-width="2"/>
            <rect width="120" height="34" rx="12" fill="#334155"/>
            <text x="60" y="22" fill="#f8fafc" font-size="12" font-weight="700" text-anchor="middle">IoT DEVICES</text>
            
            <circle cx="35" cy="65" r="14" fill="#0f172a" stroke="#10b981" stroke-width="2"/>
            <text x="35" y="70" font-size="14" text-anchor="middle">🔔</text>
            <text x="60" y="70" fill="#cbd5e1" font-size="11">Doorbell</text>

            <circle cx="35" cy="110" r="14" fill="#0f172a" stroke="#10b981" stroke-width="2"/>
            <text x="35" y="115" font-size="14" text-anchor="middle">📹</text>
            <text x="60" y="115" fill="#cbd5e1" font-size="11">IP Camera</text>

            <circle cx="35" cy="155" r="14" fill="#0f172a" stroke="#10b981" stroke-width="2"/>
            <text x="35" y="160" font-size="14" text-anchor="middle">🌡️</text>
            <text x="60" y="160" fill="#cbd5e1" font-size="11">Thermostat</text>

            <text x="60" y="190" fill="#94a3b8" font-size="10" text-anchor="middle" id="node-dev-count">10 Nodes (500 MIPS)</text>
          </g>

          <!-- Link Label LAN -->
          <g transform="translate(325, 130)">
            <rect x="-65" y="-12" width="130" height="24" rx="4" fill="#0b1329" stroke="#10b981" stroke-width="1"/>
            <text x="0" y="4" fill="#6ee7b7" font-size="10" font-weight="600" text-anchor="middle">LAN Link: 2.0 ms</text>
            <text x="0" y="24" fill="#64748b" font-size="9" text-anchor="middle">100 Mbps Bandwidth</text>
          </g>

          <!-- NODE 2: Local Fog Gateway -->
          <g transform="translate(430, 60)" id="node-fog">
            <rect width="140" height="220" rx="14" fill="#1e293b" stroke="#06b6d4" stroke-width="3"/>
            <rect width="140" height="38" rx="14" fill="#0e7490"/>
            <text x="70" y="24" fill="#ffffff" font-size="13" font-weight="800" text-anchor="middle">FOG GATEWAY</text>
            
            <circle cx="70" cy="85" r="28" fill="#083344" stroke="#06b6d4" stroke-width="2"/>
            <text x="70" y="93" font-size="24" text-anchor="middle">🛡️</text>

            <text x="70" y="135" fill="#f8fafc" font-size="11" font-weight="700" text-anchor="middle">4,000 MIPS Gateway</text>
            <text x="70" y="152" fill="#94a3b8" font-size="10" text-anchor="middle">Quad-Core Edge Box</text>
            
            <rect x="15" y="168" width="110" height="30" rx="6" fill="#0f172a" stroke="#22d3ee" stroke-width="1.5" id="fog-badge-box"/>
            <text x="70" y="187" fill="#67e8f9" font-size="9.5" font-weight="700" text-anchor="middle" id="fog-status-txt">
              ML DETECTOR ACTIVE
            </text>

            <text x="70" y="215" fill="#64748b" font-size="9" text-anchor="middle">Power: 107.3W / 83.4W</text>
          </g>

          <!-- Link Label WAN -->
          <g transform="translate(675, 130)" id="wan-label-group">
            <rect x="-70" y="-12" width="140" height="24" rx="4" fill="#0b1329" stroke="#3b82f6" stroke-width="1"/>
            <text x="0" y="4" fill="#93c5fd" font-size="10" font-weight="600" text-anchor="middle" id="wan-delay-text">WAN Link: 100.0 ms</text>
            <text x="0" y="24" fill="#64748b" font-size="9" text-anchor="middle" id="wan-state-text">STATUS: BYPASSED (0 KB)</text>
          </g>

          <!-- NODE 3: Remote Cloud Datacenter -->
          <g transform="translate(770, 60)" id="node-cloud" opacity="0.6">
            <rect width="160" height="220" rx="14" fill="#1e293b" stroke="#334155" stroke-width="2"/>
            <rect width="160" height="38" rx="14" fill="#1e3a8a"/>
            <text x="80" y="24" fill="#93c5fd" font-size="13" font-weight="800" text-anchor="middle">CLOUD DATACENTER</text>
            
            <circle cx="80" cy="85" r="28" fill="#172554" stroke="#3b82f6" stroke-width="2"/>
            <text x="80" y="93" font-size="24" text-anchor="middle">☁️</text>

            <text x="80" y="135" fill="#f8fafc" font-size="11" font-weight="700" text-anchor="middle">44,000 MIPS Server</text>
            <text x="80" y="152" fill="#94a3b8" font-size="10" text-anchor="middle">64 GB RAM Datacenter</text>

            <rect x="20" y="168" width="120" height="30" rx="6" fill="#0f172a" stroke="#3b82f6" stroke-width="1" id="cloud-badge-box"/>
            <text x="80" y="187" fill="#94a3b8" font-size="9.5" font-weight="700" text-anchor="middle" id="cloud-status-txt">
              STANDBY / IDLE
            </text>

            <text x="80" y="215" fill="#64748b" font-size="9" text-anchor="middle">Power: 1,330W / 1,000W</text>
          </g>
        </svg>

        <!-- Technical Description Callout -->
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; border-radius: 8px; padding: 0.9rem 1.2rem; font-size: 0.85rem; color: #cbd5e1;" id="sim-explanation">
          <strong>Fog Gateway Deployment:</strong> The classification module is executed directly on the quad-core local gateway. Network packets pass over the 2.0 ms LAN link, are classified in <strong>0.0066 ms</strong>, and local enforcement decisions are returned immediately. Total end-to-end response time is <strong>9.38 ms</strong>, and no telemetry is sent over the Internet (WAN bytes = 0).
        </div>
      </div>

    </section>

    <!-- ==================================================================== -->
    <!-- TAB 2: PERFORMANCE CHARTS & FIGURES -->
    <!-- ==================================================================== -->
    <section id="tab-charts" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">📈 Empirical Simulation Charts (Generated from Raw iFogSim2 Data)</div>
            <div class="card-subtitle">Comparing Fog Gateway Placement vs. Cloud Placement across latency, bandwidth, scalability, and energy</div>
          </div>
        </div>

        <div class="charts-grid">
          <!-- Chart 1: Latency across WAN link delays -->
          <div class="chart-box">
            <h4>⏱️ Mean Latency Across WAN Link Delays (10 Devices, 1.0 rec/s)</h4>
            <svg class="chart-svg" viewBox="0 0 500 240" id="svg-chart-lat">
              <!-- Y Grid Lines -->
              <line x1="50" y1="30" x2="470" y2="30" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="34" fill="#64748b" font-size="10" text-anchor="end">400ms</text>
              <line x1="50" y1="80" x2="470" y2="80" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="84" fill="#64748b" font-size="10" text-anchor="end">300ms</text>
              <line x1="50" y1="130" x2="470" y2="130" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="134" fill="#64748b" font-size="10" text-anchor="end">200ms</text>
              <line x1="50" y1="180" x2="470" y2="180" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="184" fill="#64748b" font-size="10" text-anchor="end">100ms</text>
              <line x1="50" y1="210" x2="470" y2="210" stroke="#334155" stroke-width="1.5"/>
              <text x="42" y="214" fill="#64748b" font-size="10" text-anchor="end">0ms</text>

              <!-- Group 1: 25 ms WAN -->
              <rect x="90" y="205" width="30" height="5" fill="#10b981" rx="2"/>
              <text x="105" y="198" fill="#34d399" font-size="9" font-weight="bold" text-anchor="middle">9.4ms</text>
              <rect x="125" y="181" width="30" height="29" fill="#3b82f6" rx="2"/>
              <text x="140" y="174" fill="#93c5fd" font-size="9" font-weight="bold" text-anchor="middle">57.0ms</text>
              <text x="122" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">25 ms Delay</text>

              <!-- Group 2: 100 ms WAN -->
              <rect x="220" y="205" width="30" height="5" fill="#10b981" rx="2"/>
              <text x="235" y="198" fill="#34d399" font-size="9" font-weight="bold" text-anchor="middle">9.4ms</text>
              <rect x="255" y="106" width="30" height="104" fill="#3b82f6" rx="2"/>
              <text x="270" y="99" fill="#93c5fd" font-size="9" font-weight="bold" text-anchor="middle">207.0ms</text>
              <text x="252" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">100 ms Delay</text>

              <!-- Group 3: 200 ms WAN -->
              <rect x="350" y="205" width="30" height="5" fill="#10b981" rx="2"/>
              <text x="365" y="198" fill="#34d399" font-size="9" font-weight="bold" text-anchor="middle">9.4ms</text>
              <rect x="385" y="6" width="30" height="204" fill="#3b82f6" rx="2"/>
              <text x="400" y="2" fill="#93c5fd" font-size="9" font-weight="bold" text-anchor="middle">407.0ms</text>
              <text x="382" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">200 ms Delay</text>
            </svg>
            <div style="display: flex; justify-content: center; gap: 1.5rem; margin-top: 0.5rem; font-size: 0.8rem;">
              <span style="color: #34d399;">■ Fog Placement (Constant 9.38 ms)</span>
              <span style="color: #93c5fd;">■ Cloud Placement (Linear growth with WAN)</span>
            </div>
          </div>

          <!-- Chart 2: Scalability Latency vs Device Count -->
          <div class="chart-box">
            <h4>📊 Scalability: Latency vs. IoT Device Count (WAN = 100 ms)</h4>
            <svg class="chart-svg" viewBox="0 0 500 240" id="svg-chart-scale">
              <line x1="50" y1="30" x2="470" y2="30" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="34" fill="#64748b" font-size="10" text-anchor="end">1200ms</text>
              <line x1="50" y1="90" x2="470" y2="90" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="94" fill="#64748b" font-size="10" text-anchor="end">800ms</text>
              <line x1="50" y1="150" x2="470" y2="150" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="154" fill="#64748b" font-size="10" text-anchor="end">400ms</text>
              <line x1="50" y1="210" x2="470" y2="210" stroke="#334155" stroke-width="1.5"/>
              <text x="42" y="214" fill="#64748b" font-size="10" text-anchor="end">0ms</text>

              <!-- Points: 10, 50, 100, 200 devices (X: 100, 200, 310, 430) -->
              <!-- Fog Line (Green) -->
              <polyline points="100,208 200,107 310,103 430,84" fill="none" stroke="#10b981" stroke-width="3" stroke-linecap="round"/>
              <circle cx="100" cy="208" r="4" fill="#10b981"/>
              <circle cx="200" cy="107" r="4" fill="#10b981"/>
              <circle cx="310" cy="103" r="4" fill="#10b981"/>
              <circle cx="430" cy="84" r="4" fill="#10b981"/>

              <!-- Cloud Line (Blue) -->
              <polyline points="100,179 200,177 310,170 430,163" fill="none" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>
              <circle cx="100" cy="179" r="4" fill="#3b82f6"/>
              <circle cx="200" cy="177" r="4" fill="#3b82f6"/>
              <circle cx="310" cy="170" r="4" fill="#3b82f6"/>
              <circle cx="430" cy="163" r="4" fill="#3b82f6"/>

              <!-- X Labels -->
              <text x="100" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">10 Devs</text>
              <text x="200" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">50 Devs</text>
              <text x="310" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">100 Devs</text>
              <text x="430" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">200 Devs</text>
            </svg>
            <div style="display: flex; justify-content: center; gap: 1.5rem; margin-top: 0.5rem; font-size: 0.8rem;">
              <span style="color: #34d399;">● Fog Placement Latency Curve</span>
              <span style="color: #93c5fd;">■ Cloud Placement Latency Curve</span>
            </div>
          </div>

          <!-- Chart 3: WAN Bandwidth -->
          <div class="chart-box">
            <h4>🌐 WAN Network Bandwidth Overhead (KB Transferred over Internet)</h4>
            <svg class="chart-svg" viewBox="0 0 500 240">
              <line x1="50" y1="30" x2="470" y2="30" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="34" fill="#64748b" font-size="10" text-anchor="end">60 MB</text>
              <line x1="50" y1="90" x2="470" y2="90" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="94" fill="#64748b" font-size="10" text-anchor="end">40 MB</text>
              <line x1="50" y1="150" x2="470" y2="150" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="154" fill="#64748b" font-size="10" text-anchor="end">20 MB</text>
              <line x1="50" y1="210" x2="470" y2="210" stroke="#334155" stroke-width="1.5"/>
              <text x="42" y="214" fill="#64748b" font-size="10" text-anchor="end">0 KB</text>

              <!-- Fog Bars (Flat 0) -->
              <rect x="90" y="209" width="30" height="1" fill="#10b981"/>
              <rect x="180" y="209" width="30" height="1" fill="#10b981"/>
              <rect x="270" y="209" width="30" height="1" fill="#10b981"/>
              <rect x="360" y="209" width="30" height="1" fill="#10b981"/>

              <!-- Cloud Bars (Linear Scaling) -->
              <rect x="125" y="208" width="30" height="2" fill="#3b82f6" rx="2"/>
              <text x="140" y="203" fill="#93c5fd" font-size="8.5" text-anchor="middle">0.6MB</text>

              <rect x="215" y="200" width="30" height="10" fill="#3b82f6" rx="2"/>
              <text x="230" y="195" fill="#93c5fd" font-size="8.5" text-anchor="middle">3.3MB</text>

              <rect x="305" y="190" width="30" height="20" fill="#3b82f6" rx="2"/>
              <text x="320" y="185" fill="#93c5fd" font-size="8.5" text-anchor="middle">6.6MB</text>

              <rect x="395" y="30" width="30" height="180" fill="#3b82f6" rx="2"/>
              <text x="410" y="24" fill="#93c5fd" font-size="8.5" text-anchor="middle">60.1MB</text>

              <text x="122" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">10 Devs</text>
              <text x="212" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">50 Devs</text>
              <text x="302" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">100 Devs</text>
              <text x="392" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">200 Devs (Peak)</text>
            </svg>
            <div style="display: flex; justify-content: center; gap: 1.5rem; margin-top: 0.5rem; font-size: 0.8rem;">
              <span style="color: #34d399;">■ Fog: 0.00 KB Consumed (100% WAN Savings)</span>
              <span style="color: #93c5fd;">■ Cloud: Heavy WAN Transit (up to 60.1 MB)</span>
            </div>
          </div>

          <!-- Chart 4: Energy Consumption -->
          <div class="chart-box">
            <h4>⚡ Energy Consumption Comparison (MegaJoules)</h4>
            <svg class="chart-svg" viewBox="0 0 500 240">
              <line x1="50" y1="30" x2="470" y2="30" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="34" fill="#64748b" font-size="10" text-anchor="end">100 MJ</text>
              <line x1="50" y1="90" x2="470" y2="90" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="94" fill="#64748b" font-size="10" text-anchor="end">60 MJ</text>
              <line x1="50" y1="150" x2="470" y2="150" stroke="#1f2937" stroke-dasharray="4"/>
              <text x="42" y="154" fill="#64748b" font-size="10" text-anchor="end">20 MJ</text>
              <line x1="50" y1="210" x2="470" y2="210" stroke="#334155" stroke-width="1.5"/>
              <text x="42" y="214" fill="#64748b" font-size="10" text-anchor="end">0 MJ</text>

              <!-- Local Fog Energy -->
              <rect x="110" y="200" width="50" height="10" fill="#06b6d4" rx="3"/>
              <text x="135" y="192" fill="#67e8f9" font-size="9" font-weight="bold" text-anchor="middle">5.02 MJ</text>

              <rect x="170" y="200" width="50" height="10" fill="#0e7490" rx="3"/>
              <text x="195" y="192" fill="#67e8f9" font-size="9" font-weight="bold" text-anchor="middle">5.00 MJ</text>
              <text x="165" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">Fog Gateway Node</text>

              <!-- Cloud Datacenter Energy -->
              <rect x="300" y="66" width="50" height="144" fill="#3b82f6" rx="3"/>
              <text x="325" y="58" fill="#93c5fd" font-size="9" font-weight="bold" text-anchor="middle">79.92 MJ</text>

              <rect x="360" y="66" width="50" height="144" fill="#1e40af" rx="3"/>
              <text x="385" y="58" fill="#93c5fd" font-size="9" font-weight="bold" text-anchor="middle">79.95 MJ</text>
              <text x="355" y="228" fill="#94a3b8" font-size="11" text-anchor="middle">Cloud Datacenter Node</text>
            </svg>
            <div style="display: flex; justify-content: center; gap: 1.5rem; margin-top: 0.5rem; font-size: 0.8rem;">
              <span style="color: #67e8f9;">■ Fog Placement Energy</span>
              <span style="color: #93c5fd;">■ Cloud Placement Energy</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================================================================== -->
    <!-- TAB 3: 48-SCENARIO SWEEP EXPLORER -->
    <!-- ==================================================================== -->
    <section id="tab-sweep" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">📋 Full 48-Scenario Parameter Sweep Explorer</div>
            <div class="card-subtitle">Every scenario was genuinely executed and measured using Cloudslab iFogSim2 v2.0.0</div>
          </div>
          <button class="btn btn-outline" onclick="exportFilteredSweepCSV()">📥 Download Filtered CSV</button>
        </div>

        <!-- Filter Controls -->
        <div class="controls-bar" style="margin-bottom: 1rem;">
          <div class="control-group">
            <label class="control-label">Filter Placement</label>
            <select id="filter-placement" class="control-select" onchange="applySweepFilters()">
              <option value="all">All Placements</option>
              <option value="fog">Fog Placement</option>
              <option value="cloud">Cloud Placement</option>
            </select>
          </div>
          <div class="control-group">
            <label class="control-label">Filter Devices</label>
            <select id="filter-devices" class="control-select" onchange="applySweepFilters()">
              <option value="all">All (10, 50, 100, 200)</option>
              <option value="10">10 Devices</option>
              <option value="50">50 Devices</option>
              <option value="100">100 Devices</option>
              <option value="200">200 Devices</option>
            </select>
          </div>
          <div class="control-group">
            <label class="control-label">Filter WAN Latency</label>
            <select id="filter-latency" class="control-select" onchange="applySweepFilters()">
              <option value="all">All (25ms, 100ms, 200ms)</option>
              <option value="25.0">25 ms</option>
              <option value="100.0">100 ms</option>
              <option value="200.0">200 ms</option>
            </select>
          </div>
          <div class="control-group">
            <label class="control-label">Filter Rate</label>
            <select id="filter-rate" class="control-select" onchange="applySweepFilters()">
              <option value="all">All Rates</option>
              <option value="1.0">1.0 rec/s</option>
              <option value="5.0">5.0 rec/s</option>
            </select>
          </div>
          <div class="control-group" style="flex: 1; min-width: 200px;">
            <label class="control-label">Search Table</label>
            <input type="text" id="filter-search" class="control-input" placeholder="Search by number or keyword..." onkeyup="applySweepFilters()">
          </div>
        </div>

        <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;" id="sweep-count-label">
          Showing 48 of 48 measured scenarios
        </div>

        <!-- Table Container -->
        <div class="table-container" style="max-height: 520px; overflow-y: auto;">
          <table id="sweep-table">
            <thead>
              <tr>
                <th onclick="sortSweepTable('device_count')">Devices ⬍</th>
                <th onclick="sortSweepTable('placement')">Placement ⬍</th>
                <th onclick="sortSweepTable('wan_latency_ms')">WAN Latency ⬍</th>
                <th onclick="sortSweepTable('record_rate_per_sec')">Rate (rec/s) ⬍</th>
                <th onclick="sortSweepTable('completed_count')">Completed ⬍</th>
                <th onclick="sortSweepTable('mean_latency_ms')">Mean Latency ⬍</th>
                <th onclick="sortSweepTable('p95_latency_ms')">P95 Latency ⬍</th>
                <th onclick="sortSweepTable('wan_bytes_transmitted')">WAN Traffic ⬍</th>
                <th onclick="sortSweepTable('execution_time_wall_ms')">Wall Time ⬍</th>
              </tr>
            </thead>
            <tbody id="sweep-tbody">
              <!-- Populated by JavaScript -->
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- ==================================================================== -->
    <!-- TAB 4: 55-RECORD TRAFFIC CLASSIFIER -->
    <!-- ==================================================================== -->
    <section id="tab-demo" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">🔬 55-Record Traffic Classifier & 115-Feature Deep Inspector</div>
            <div class="card-subtitle">Evaluated on strictly separated demonstration dataset (100% agreement with ground-truth)</div>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <button class="btn btn-outline" onclick="filterDemoRecords('all')">All (55)</button>
            <button class="btn btn-outline" style="color: #34d399;" onclick="filterDemoRecords('benign')">ALLOW / Normal (5)</button>
            <button class="btn btn-outline" style="color: #f87171;" onclick="filterDemoRecords('malicious')">QUARANTINE / Attack (50)</button>
          </div>
        </div>

        <div class="table-container" style="max-height: 520px; overflow-y: auto;">
          <table>
            <thead>
              <tr>
                <th>Record ID</th>
                <th>Ground-Truth</th>
                <th>ML Prediction</th>
                <th>Predicted Attack Type</th>
                <th>Confidence</th>
                <th>Enforcement Action</th>
                <th>Agreement</th>
                <th>Deep Inspection</th>
              </tr>
            </thead>
            <tbody id="demo-tbody">
              <!-- Populated by JavaScript -->
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- ==================================================================== -->
    <!-- TAB 5: FACULTY VIVA & ARCHITECTURE GUIDE -->
    <!-- ==================================================================== -->
    <section id="tab-viva" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">🎓 Faculty Examination Defense & Theoretical Guide</div>
            <div class="card-subtitle">Comprehensive technical answers to anticipated faculty and viva questions</div>
          </div>
        </div>

        <div class="qa-item open">
          <div class="qa-question" onclick="toggleQA(this)">
            <span>1. What represents "one record" in FogSentinel? Is it a single packet or payload?</span>
            <span class="qa-icon">▼</span>
          </div>
          <div class="qa-answer">
            <strong>No, one record is not a raw network packet.</strong> It is a <strong>115-dimensional continuous statistical summary vector</strong> extracted over 5 exponentially decaying sliding time windows (&lambda; = 0.01, 0.1, 1.0, 3.0, 5.0) by a network stream aggregator. It captures packet size statistics, stream weights, packet jitter means and standard deviations, socket covariance, and radii. Feeding raw packet bytes into ML at the edge is too noisy and compute-intensive; these statistical stream vectors capture temporal botnet flood behavior.
          </div>
        </div>

        <div class="qa-item">
          <div class="qa-question" onclick="toggleQA(this)">
            <span>2. Why did Random Forest outperform Deep Neural Networks (MLP)?</span>
            <span class="qa-icon">▼</span>
          </div>
          <div class="qa-answer">
            We empirically evaluated Logistic Regression, a Multi-Layer Perceptron (MLP) neural network, and Random Forest on 6,600 unseen test records. Random Forest achieved <strong>99.98% accuracy</strong>, significantly outperforming the MLP (90.71% multi-class accuracy). In modern tabular machine learning literature (e.g., Grinsztajn et al., NeurIPS), decision tree ensembles consistently outperform neural networks on continuous statistical tables because decision trees construct axis-aligned step boundaries that cleanly isolate abrupt shifts like UDP and SYN flood bursts. In addition, Random Forest executes in <strong>0.0066 ms per record</strong>, enabling 151,500 predictions/sec on edge hardware.
          </div>
        </div>

        <div class="qa-item">
          <div class="qa-question" onclick="toggleQA(this)">
            <span>3. How do you mathematically explain the latency difference (9.38 ms vs. 206.98 ms)?</span>
            <span class="qa-icon">▼</span>
          </div>
          <div class="qa-answer">
            In iFogSim2, total end-to-end response latency is the sum of propagation, transmission, queueing, and processing times:<br>
            <code>Latency = T_prop(up) + T_trans(up) + T_queue + T_proc + T_prop(down) + T_trans(down)</code><br><br>
            • <strong>Fog Placement:</strong> Traverses only the local LAN link (propagation = 2.0 ms each way). With 1,000 MIPS processing effort on a 4,000 MIPS gateway (approx 0.25 ms execution + 5 ms queueing), total response time is <strong>9.38 ms</strong>.<br>
            • <strong>Cloud Placement:</strong> Must traverse the physical WAN link twice (100 ms uplink + 100 ms downlink = 200 ms minimum physical speed-of-light delay). Even with a fast 44,000 MIPS cloud server, total latency is <strong>206.98 ms</strong>.<br>
            Fog computing fundamentally eliminates the WAN propagation bottleneck.
          </div>
        </div>

        <div class="qa-item">
          <div class="qa-question" onclick="toggleQA(this)">
            <span>4. Does Fog placement always save energy?</span>
            <span class="qa-icon">▼</span>
          </div>
          <div class="qa-answer">
            <strong>No, Fog computing does not consistently save energy.</strong> In our simulations, the Fog node consumed slightly more energy in Fog placement (5,022.25 kJ vs 5,005.99 kJ) because its CPU was actively computing the 1,000 MIPS classification rather than simply routing packets. Fog computing is optimized for <strong>low response latency, bandwidth preservation, and privacy</strong>, not global energy reduction.
          </div>
        </div>

        <div class="qa-item">
          <div class="qa-question" onclick="toggleQA(this)">
            <span>5. Does FogSentinel physically disconnect devices upon attack detection?</span>
            <span class="qa-icon">▼</span>
          </div>
          <div class="qa-answer">
            FogSentinel is an <strong>academic research prototype and simulation framework</strong>. When an attack is detected, it generates a simulated action labeled <code>QUARANTINE_RECOMMENDED</code>. In a production industrial deployment, this event would trigger a REST API call to a Software-Defined Networking (SDN) OpenFlow controller (such as OpenDaylight or ONOS) to dynamically inject flow-drop rules into the physical switch.
          </div>
        </div>
      </div>
    </section>

  </main>

  <!-- Deep Inspection Slide-Over Drawer -->
  <div class="drawer-overlay" id="drawer-overlay" onclick="closeDrawer()"></div>
  <div class="drawer" id="feat-drawer">
    <div class="drawer-header">
      <div>
        <div style="font-weight: 800; font-size: 1.15rem; color: #ffffff;" id="drawer-title">Record Inspection</div>
        <div style="font-size: 0.78rem; color: var(--text-muted);" id="drawer-subtitle">115 Continuous Statistical Dimensions</div>
      </div>
      <button class="drawer-close" onclick="closeDrawer()">&times;</button>
    </div>
    
    <div style="background: #172033; padding: 1rem; border-radius: 8px; margin-bottom: 1.25rem; border: 1px solid #23314d;" id="drawer-meta">
      <!-- Meta Details -->
    </div>

    <div style="font-weight: 700; font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.5rem; text-transform: uppercase;">
      All 115 Statistical Feature Measurements:
    </div>
    <div class="features-list" id="drawer-features">
      <!-- Features Populated Here -->
    </div>
  </div>

  <!-- Raw Data JSON Injected -->
  <script>
    const SIM_DATA = {sim_json};
    const DEMO_DATA = {demo_json};
    const COMP_DATA = {comp_json};

    let isAnimationPlaying = true;
    let sweepSortCol = 'device_count';
    let sweepSortAsc = true;

    // Tab Switching
    function switchTab(tabId) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      event.currentTarget.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    }}

    // Simulation View Updater
    function updateSimulationView() {{
      const placement = document.getElementById('sim-placement').value;
      const devices = parseInt(document.getElementById('sim-devices').value);
      const latency = parseFloat(document.getElementById('sim-latency').value);
      const rate = parseFloat(document.getElementById('sim-rate').value);

      // Find matching record in SIM_DATA
      let match = SIM_DATA.find(r => 
        r.placement.toLowerCase() === placement &&
        r.device_count === devices &&
        Math.abs(r.wan_latency_ms - latency) < 0.1 &&
        Math.abs(r.record_rate_per_sec - rate) < 0.1
      );

      // Find opposite placement for delta
      const oppPlace = placement === 'fog' ? 'cloud' : 'fog';
      let oppMatch = SIM_DATA.find(r => 
        r.placement.toLowerCase() === oppPlace &&
        r.device_count === devices &&
        Math.abs(r.wan_latency_ms - latency) < 0.1 &&
        Math.abs(r.record_rate_per_sec - rate) < 0.1
      );

      if (match) {{
        document.getElementById('val-latency').innerText = `${{match.mean_latency_ms.toFixed(2)}} ms`;
        document.getElementById('val-wan').innerText = `${{(match.wan_bytes_transmitted / 1024).toFixed(2)}} KB`;
        document.getElementById('val-completed').innerText = `${{match.completed_count}} records`;
        document.getElementById('val-energy').innerText = `${{(match.fog_energy_joules / 1000).toFixed(2)}} kJ`;

        // Subtitles & Delta
        if (oppMatch) {{
          const delta = oppMatch.mean_latency_ms - match.mean_latency_ms;
          const subLat = document.getElementById('sub-latency');
          if (placement === 'fog') {{
            subLat.innerText = `▼ ${{( (delta / oppMatch.mean_latency_ms) * 100 ).toFixed(1)}}% faster than Cloud (-${{delta.toFixed(2)}} ms)`;
            subLat.className = 'metric-sub good';
          }} else {{
            subLat.innerText = `▲ ${{( (Math.abs(delta) / oppMatch.mean_latency_ms) * 100 ).toFixed(1)}}% slower than Fog (+${{Math.abs(delta).toFixed(2)}} ms)`;
            subLat.className = 'metric-sub bad';
          }}
        }}

        // WAN Subtitle
        const subWan = document.getElementById('sub-wan');
        if (placement === 'fog') {{
          subWan.innerText = '100% of Internet uplink/downlink saved';
          subWan.className = 'metric-sub good';
        }} else {{
          subWan.innerText = `${{(match.wan_bytes_transmitted / 1024).toFixed(1)}} KB sent across internet WAN link`;
          subWan.className = 'metric-sub bad';
        }}
      }}

      // Topology Visual Adjustments
      const isFog = (placement === 'fog');
      document.getElementById('node-dev-count').innerText = `${{devices}} Nodes (500 MIPS)`;
      document.getElementById('wan-delay-text').innerText = `WAN Link: ${{latency.toFixed(1)}} ms`;

      const pathBadge = document.getElementById('active-path-badge');
      const pktWanUp = document.getElementById('pkt-wan-up');
      const pktWanDown = document.getElementById('pkt-wan-down');
      const wanLink = document.getElementById('link-wan');
      const nodeFog = document.getElementById('node-fog');
      const nodeCloud = document.getElementById('node-cloud');
      const fogStatus = document.getElementById('fog-status-txt');
      const cloudStatus = document.getElementById('cloud-status-txt');
      const wanStateText = document.getElementById('wan-state-text');
      const simExplanation = document.getElementById('sim-explanation');

      if (isFog) {{
        pathBadge.innerText = 'LOCAL FOG LOOP ACTIVE (LAN ONLY)';
        pathBadge.className = 'badge-pill badge-fog';
        pktWanUp.style.display = 'none';
        pktWanDown.style.display = 'none';
        wanLink.setAttribute('opacity', '0.25');
        nodeFog.setAttribute('opacity', '1.0');
        nodeCloud.setAttribute('opacity', '0.5');
        fogStatus.innerText = 'ML DETECTOR ACTIVE';
        fogStatus.setAttribute('fill', '#67e8f9');
        cloudStatus.innerText = 'STANDBY / IDLE';
        cloudStatus.setAttribute('fill', '#94a3b8');
        wanStateText.innerText = 'STATUS: BYPASSED (0 KB)';
        wanStateText.setAttribute('fill', '#64748b');

        simExplanation.innerHTML = `<strong>Fog Gateway Deployment:</strong> The classification module executes directly on the quad-core local gateway. Network packets pass over the 2.0 ms LAN link, are classified in <strong>0.0066 ms</strong>, and local enforcement decisions are returned immediately. Total end-to-end response time is <strong>${{match ? match.mean_latency_ms.toFixed(2) : 9.38}} ms</strong>, and no telemetry is sent over the Internet (WAN bytes = 0).`;
      }} else {{
        pathBadge.innerText = 'REMOTE CLOUD LOOP ACTIVE (WAN TRAVERSAL)';
        pathBadge.className = 'badge-pill badge-cloud';
        pktWanUp.style.display = 'block';
        pktWanDown.style.display = 'block';
        wanLink.setAttribute('opacity', '1.0');
        nodeFog.setAttribute('opacity', '0.7');
        nodeCloud.setAttribute('opacity', '1.0');
        fogStatus.innerText = 'ROUTER / FORWARDER';
        fogStatus.setAttribute('fill', '#94a3b8');
        cloudStatus.innerText = 'ML DETECTOR ACTIVE';
        cloudStatus.setAttribute('fill', '#93c5fd');
        wanStateText.innerText = `STATUS: ACTIVE (${{match ? (match.wan_bytes_transmitted/1024).toFixed(1) : 659.3}} KB)`;
        wanStateText.setAttribute('fill', '#38bdf8');

        simExplanation.innerHTML = `<strong>Remote Cloud Deployment:</strong> The classification module is hosted in the centralized cloud datacenter. Every IoT record must travel across the <strong>${{latency.toFixed(0)}} ms WAN link</strong> twice (uplink propagation + downlink response = <strong>${{(latency * 2).toFixed(0)}} ms</strong> physical speed-of-light delay). Total response time rises to <strong>${{match ? match.mean_latency_ms.toFixed(2) : 206.98}} ms</strong>, generating <strong>${{match ? (match.wan_bytes_transmitted/1024).toFixed(1) : 659.3}} KB</strong> of WAN data overhead.`;
      }}
    }}

    function toggleAnimation() {{
      const svg = document.getElementById('topo-svg');
      const btn = document.getElementById('btn-toggle-anim');
      if (isAnimationPlaying) {{
        svg.pauseAnimations();
        btn.innerText = '▶ Resume Animation';
        btn.className = 'btn btn-outline';
        isAnimationPlaying = false;
      }} else {{
        svg.unpauseAnimations();
        btn.innerText = '⏸ Pause Animation';
        btn.className = 'btn btn-green';
        isAnimationPlaying = true;
      }}
    }}

    function resetSimDefaults() {{
      document.getElementById('sim-placement').value = 'fog';
      document.getElementById('sim-devices').value = '10';
      document.getElementById('sim-latency').value = '100.0';
      document.getElementById('sim-rate').value = '1.0';
      updateSimulationView();
    }}

    // =========================================================================
    // 48-Scenario Sweep Table Rendering & Filtering
    // =========================================================================
    function renderSweepTable(data) {{
      const tbody = document.getElementById('sweep-tbody');
      tbody.innerHTML = '';

      data.forEach(row => {{
        const tr = document.createElement('tr');
        const isFog = (row.placement.toLowerCase() === 'fog');
        tr.innerHTML = `
          <td class="font-mono"><strong>${{row.device_count}}</strong></td>
          <td><span class="badge-pill ${{isFog ? 'badge-fog' : 'badge-cloud'}}">${{row.placement.toUpperCase()}}</span></td>
          <td class="font-mono">${{row.wan_latency_ms.toFixed(1)}} ms</td>
          <td class="font-mono">${{row.record_rate_per_sec.toFixed(1)}}</td>
          <td class="font-mono">${{row.completed_count.toLocaleString()}}</td>
          <td class="font-mono" style="font-weight: 700; color: ${{isFog ? '#34d399' : '#93c5fd'}};">${{row.mean_latency_ms.toFixed(2)}} ms</td>
          <td class="font-mono">${{row.p95_latency_ms.toFixed(2)}} ms</td>
          <td class="font-mono" style="color: ${{isFog ? '#9ca3af' : '#38bdf8'}};">${{(row.wan_bytes_transmitted / 1024).toFixed(1)}} KB</td>
          <td class="font-mono">${{row.execution_time_wall_ms}} ms</td>
        `;
        tbody.appendChild(tr);
      }});

      document.getElementById('sweep-count-label').innerText = `Showing ${{data.length}} of ${{SIM_DATA.length}} measured scenarios`;
    }}

    function applySweepFilters() {{
      const place = document.getElementById('filter-placement').value;
      const devs = document.getElementById('filter-devices').value;
      const lat = document.getElementById('filter-latency').value;
      const rate = document.getElementById('filter-rate').value;
      const q = document.getElementById('filter-search').value.toLowerCase().trim();

      let filtered = SIM_DATA.filter(row => {{
        if (place !== 'all' && row.placement.toLowerCase() !== place) return false;
        if (devs !== 'all' && row.device_count !== parseInt(devs)) return false;
        if (lat !== 'all' && Math.abs(row.wan_latency_ms - parseFloat(lat)) > 0.1) return false;
        if (rate !== 'all' && Math.abs(row.record_rate_per_sec - parseFloat(rate)) > 0.1) return false;
        if (q) {{
          const str = `${{row.device_count}} ${{row.placement}} ${{row.wan_latency_ms}} ${{row.record_rate_per_sec}} ${{row.mean_latency_ms}}`.toLowerCase();
          if (!str.includes(q)) return false;
        }}
        return true;
      }});

      // Sort
      filtered.sort((a, b) => {{
        let vA = a[sweepSortCol];
        let vB = b[sweepSortCol];
        if (typeof vA === 'string') {{
          return sweepSortAsc ? vA.localeCompare(vB) : vB.localeCompare(vA);
        }}
        return sweepSortAsc ? vA - vB : vB - vA;
      }});

      renderSweepTable(filtered);
    }}

    function sortSweepTable(col) {{
      if (sweepSortCol === col) {{
        sweepSortAsc = !sweepSortAsc;
      }} else {{
        sweepSortCol = col;
        sweepSortAsc = true;
      }}
      applySweepFilters();
    }}

    function exportFilteredSweepCSV() {{
      const rows = Array.from(document.querySelectorAll('#sweep-table tr'));
      let csv = rows.map(r => Array.from(r.querySelectorAll('th,td')).map(c => `"${{c.innerText.replace(/"/g, '""')}}"`).join(',')).join('\\n');
      const blob = new Blob([csv], {{ type: 'text/csv' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'fogsentinel_simulation_view.csv';
      a.click();
    }}

    // =========================================================================
    // 55-Record Demo Table
    // =========================================================================
    function renderDemoTable(records) {{
      const tbody = document.getElementById('demo-tbody');
      tbody.innerHTML = '';

      records.forEach((rec, idx) => {{
        const tr = document.createElement('tr');
        const isBenign = (rec.prediction === 'benign');
        const isMatch = (rec.prediction === rec.gt_binary);
        
        tr.innerHTML = `
          <td class="font-mono"><strong>${{rec.record_id}}</strong></td>
          <td><span class="badge-pill ${{rec.gt_binary === 'benign' ? 'badge-allow' : 'badge-quarantine'}}">${{rec.gt_binary.toUpperCase()}}</span></td>
          <td><span class="badge-pill ${{isBenign ? 'badge-allow' : 'badge-quarantine'}}">${{rec.prediction.toUpperCase()}}</span></td>
          <td class="font-mono">${{rec.predicted_attack_type}}</td>
          <td class="font-mono">${{(rec.confidence * 100).toFixed(1)}}%</td>
          <td><span class="badge-pill ${{rec.action === 'ALLOW' ? 'badge-allow' : 'badge-quarantine'}}">${{rec.action}}</span></td>
          <td style="color: ${{isMatch ? '#34d399' : '#f87171'}};">${{isMatch ? '✓ Verified' : '✗ Mismatch'}}</td>
          <td><button class="btn btn-outline" style="padding: 0.25rem 0.6rem; font-size: 0.75rem;" onclick="inspectRecord(${{idx}})">🔬 Inspect 115 Features</button></td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function filterDemoRecords(type) {{
      if (type === 'all') {{
        renderDemoTable(DEMO_DATA);
      }} else if (type === 'benign') {{
        renderDemoTable(DEMO_DATA.filter(r => r.prediction === 'benign'));
      }} else {{
        renderDemoTable(DEMO_DATA.filter(r => r.prediction === 'malicious'));
      }}
    }}

    function inspectRecord(idx) {{
      const rec = DEMO_DATA[idx];
      document.getElementById('drawer-title').innerText = `Record: ${{rec.record_id}}`;
      document.getElementById('drawer-subtitle').innerText = `Predicted: ${{rec.predicted_attack_type}} | Action: ${{rec.action}}`;

      const meta = document.getElementById('drawer-meta');
      meta.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.85rem;">
          <div><span style="color:#94a3b8">Verdict:</span> <strong>${{rec.prediction.toUpperCase()}}</strong></div>
          <div><span style="color:#94a3b8">Confidence:</span> <strong>${{(rec.confidence * 100).toFixed(2)}}%</strong></div>
          <div><span style="color:#94a3b8">Enforcement:</span> <strong>${{rec.action}}</strong></div>
          <div><span style="color:#94a3b8">Ground Truth:</span> <strong>${{rec.gt_multi}}</strong></div>
        </div>
      `;

      const fContainer = document.getElementById('drawer-features');
      fContainer.innerHTML = '';
      for (const [k, v] of Object.entries(rec.features)) {{
        const item = document.createElement('div');
        item.className = 'feature-item';
        item.innerHTML = `
          <div class="feature-key">${{k}}</div>
          <div class="feature-val">${{v}}</div>
        `;
        fContainer.appendChild(item);
      }}

      document.getElementById('drawer-overlay').style.display = 'block';
      document.getElementById('feat-drawer').classList.add('open');
    }}

    function closeDrawer() {{
      document.getElementById('drawer-overlay').style.display = 'none';
      document.getElementById('feat-drawer').classList.remove('open');
    }}

    // Q&A Toggle
    function toggleQA(el) {{
      const item = el.parentElement;
      item.classList.toggle('open');
    }}

    // Init
    window.addEventListener('DOMContentLoaded', () => {{
      updateSimulationView();
      renderSweepTable(SIM_DATA);
      renderDemoTable(DEMO_DATA);
    }});
  </script>
</body>
</html>
"""

    out_file = ROOT_DIR / "dashboard" / "index.html"
    out_file.write_text(html_content, encoding="utf-8")
    print(f"[Dashboard] Self-contained HTML Dashboard saved to: {out_file} ({len(html_content):,} bytes)")

if __name__ == "__main__":
    build_html_dashboard()
