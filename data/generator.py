"""Shared synthetic data generator for AIOps demo."""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

rng = np.random.default_rng(42)

# ── Log levels & services ──────────────────────────────────────────────────────
SERVICES  = ["api-gateway", "auth-service", "db-proxy", "ml-pipeline",
             "kafka-broker", "log-collector", "alert-manager", "grafana"]
LEVELS    = ["INFO", "INFO", "INFO", "WARN", "ERROR", "DEBUG"]
MESSAGES  = {
    "INFO":  ["Request processed successfully", "Connection established",
              "Batch ingestion completed", "Model inference done",
              "Health check passed", "Cache hit ratio: {v}%"],
    "WARN":  ["High memory usage: {v}%", "Slow query detected: {v}ms",
              "Retry attempt #{v}", "Connection pool near limit",
              "Rate limit approaching: {v} req/s"],
    "ERROR": ["Connection refused on port {v}", "OOMKill detected on pod",
              "Anomaly score threshold exceeded: {v}",
              "Pipeline stage failed after {v} retries",
              "Kafka consumer lag: {v}k messages"],
    "DEBUG": ["Trace: span_id={v}", "Feature vector shape: ({v}, 128)",
              "Checkpoint saved at epoch {v}"],
}

def _msg(level):
    tmpl = random.choice(MESSAGES[level])
    return tmpl.replace("{v}", str(random.randint(50, 999)))


def generate_logs(n=200):
    now = datetime.utcnow()
    rows = []
    for i in range(n):
        ts   = now - timedelta(seconds=(n - i) * random.uniform(0.5, 3))
        lvl  = random.choice(LEVELS)
        rows.append({
            "timestamp": ts,
            "level":     lvl,
            "service":   random.choice(SERVICES),
            "message":   _msg(lvl),
            "latency_ms": rng.integers(5, 2000),
            "anomaly_score": round(float(rng.uniform(0.0, 1.0)), 3),
        })
    df = pd.DataFrame(rows).sort_values("timestamp", ascending=False)
    return df


def generate_timeseries(hours=24, freq_min=5):
    periods = int(hours * 60 / freq_min)
    idx = pd.date_range(end=datetime.utcnow(), periods=periods, freq=f"{freq_min}min")
    df = pd.DataFrame(index=idx)
    df["log_volume"]      = (rng.integers(800, 1500, periods)
                              + 300 * np.sin(np.linspace(0, 4*np.pi, periods))).astype(int)
    df["error_rate"]      = rng.uniform(0.5, 8, periods).round(2)
    df["anomaly_count"]   = rng.integers(0, 12, periods)
    df["cpu_usage"]       = (50 + 20 * np.sin(np.linspace(0, 6*np.pi, periods))
                              + rng.normal(0, 5, periods)).clip(10, 95).round(1)
    df["memory_usage"]    = (60 + 15 * np.cos(np.linspace(0, 4*np.pi, periods))
                              + rng.normal(0, 4, periods)).clip(20, 95).round(1)
    df["latency_p99"]     = (rng.integers(80, 400, periods)
                              + 200 * (df["anomaly_count"] > 5).astype(int))
    return df


def generate_anomalies(n=80):
    now = datetime.utcnow()
    types = ["CPU Spike", "Memory Leak", "OOMKill", "Disk I/O Surge",
             "Network Timeout", "Kafka Lag", "Pod CrashLoop", "Auth Failure"]
    rows = []
    for _ in range(n):
        atype = random.choice(types)
        score = round(float(rng.uniform(0.6, 1.0)), 3)
        rows.append({
            "timestamp":  now - timedelta(hours=random.uniform(0, 48)),
            "type":       atype,
            "service":    random.choice(SERVICES),
            "score":      score,
            "severity":   "CRITICAL" if score > 0.85 else "HIGH" if score > 0.72 else "MEDIUM",
            "resolved":   random.choice([True, True, False]),
            "ttd_min":    random.randint(1, 45),   # time-to-detect
            "ttr_min":    random.randint(5, 120),  # time-to-resolve
        })
    return pd.DataFrame(rows).sort_values("timestamp", ascending=False)


def generate_nodes():
    """For 3-D infrastructure graph."""
    nodes = []
    for i, svc in enumerate(SERVICES):
        angle   = 2 * np.pi * i / len(SERVICES)
        tier    = 0 if "gateway" in svc else (1 if "service" in svc or "auth" in svc else 2)
        r       = [1.5, 3.0, 4.5][tier]
        health  = random.choice(["healthy","healthy","healthy","warn","critical"])
        nodes.append({
            "id": svc,
            "x": r * np.cos(angle) + rng.uniform(-0.3, 0.3),
            "y": r * np.sin(angle) + rng.uniform(-0.3, 0.3),
            "z": tier * 2.0 + rng.uniform(-0.4, 0.4),
            "tier": tier,
            "health": health,
            "cpu": random.randint(20, 90),
            "mem": random.randint(30, 85),
        })
    return pd.DataFrame(nodes)


def generate_model_metrics():
    epochs = np.arange(1, 51)
    return pd.DataFrame({
        "epoch":        epochs,
        "train_loss":   (1.5 * np.exp(-0.08 * epochs) + rng.normal(0, 0.02, 50)).clip(0),
        "val_loss":     (1.6 * np.exp(-0.07 * epochs) + rng.normal(0, 0.03, 50)).clip(0),
        "precision":    (1 - 0.8 * np.exp(-0.1 * epochs) + rng.normal(0, 0.01, 50)).clip(0, 1),
        "recall":       (1 - 0.85 * np.exp(-0.09 * epochs) + rng.normal(0, 0.01, 50)).clip(0, 1),
        "f1":           (1 - 0.82 * np.exp(-0.095 * epochs) + rng.normal(0, 0.01, 50)).clip(0, 1),
    })
