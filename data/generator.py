"""
Real data loader + synthetic fallback for AIOps UI.
Parses system_logs.txt when available, else uses synthetic data.
"""
import re
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import random

SERVICES = ["api-gateway", "auth-service", "db-proxy", "ml-pipeline",
            "log-collector", "kafka-broker"]

LOG_FILE = os.path.join(os.path.dirname(__file__), "system_logs.txt")

def _categorize(msg):
    if any(k in msg for k in ["Database","Query","Transaction","disk space","connection"]):
        return "db-proxy"
    if any(k in msg for k in ["API request","Rate limit","User session","User logged","Cache miss"]):
        return "api-gateway"
    if any(k in msg for k in ["Unauthorized","Brute force","Failed login","account locked",
                               "Suspicious IP","User changed password","User updated"]):
        return "auth-service"
    if any(k in msg for k in ["Memory","CPU","Disk write","High I/O"]):
        return "ml-pipeline"
    if any(k in msg for k in ["Service health","Service restart","Dependency",
                               "Network latency","Failed to load","Unhandled exception"]):
        return "log-collector"
    return "kafka-broker"

def _anomaly_score(level, msg):
    base  = {"INFO":0.10,"WARNING":0.50,"ERROR":0.75,"CRITICAL":0.95}.get(level, 0.10)
    boost = 0.0
    if "CPU usage at 95%"           in msg: boost += 0.15
    if "Transaction rollback"        in msg: boost += 0.10
    if "Database connection failed"  in msg: boost += 0.10
    if "Brute force"                 in msg: boost += 0.10
    if "account locked"              in msg: boost += 0.10
    if "Unhandled exception"         in msg: boost += 0.10
    if "Service health check failed" in msg: boost += 0.05
    if "Memory usage exceeded"       in msg: boost += 0.10
    if "High I/O"                    in msg: boost += 0.08
    if "Disk write failure"          in msg: boost += 0.07
    return min(1.0, round(base + boost, 3))

def _latency_from_msg(msg):
    if "Slow query"  in msg: return random.randint(800, 3000)
    if "High I/O"    in msg: return random.randint(500, 1500)
    if "API request" in msg: return random.randint(50, 400)
    if "Database"    in msg: return random.randint(10, 200)
    return random.randint(5, 300)

def _parse_logs(path):
    logs = []
    pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) (.+)')
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            m = pattern.match(line)
            if m:
                ts_str, level, msg = m.groups()
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                logs.append({
                    "timestamp":     ts,
                    "level":         level,
                    "service":       _categorize(msg),
                    "message":       msg,
                    "anomaly_score": _anomaly_score(level, msg),
                    "latency_ms":    _latency_from_msg(msg),
                })
    return logs

_PARSED = None
def _get_all():
    global _PARSED
    if _PARSED is None:
        if os.path.exists(LOG_FILE):
            _PARSED = _parse_logs(LOG_FILE)
        else:
            _PARSED = _synthetic_logs(500)
    return _PARSED

def generate_logs(n=200):
    data = _get_all()
    sample = sorted(data, key=lambda x: x["timestamp"], reverse=True)[:n]
    return pd.DataFrame(sample)

def generate_timeseries(hours=24, freq_min=1):
    data = _get_all()
    if not data:
        return _synthetic_timeseries(hours, freq_min)
    by_minute = defaultdict(lambda: defaultdict(int))
    for log in data:
        key = log["timestamp"].replace(second=0, microsecond=0)
        by_minute[key]["total"] += 1
        by_minute[key][log["level"]] += 1
        if log["anomaly_score"] >= 0.75:
            by_minute[key]["anomaly"] += 1
    rows = []
    for ts in sorted(by_minute.keys()):
        d = by_minute[ts]
        nearby = [l for l in data if abs((l["timestamp"]-ts).total_seconds()) < 60]
        cpu_hits = sum(1 for l in nearby if "CPU" in l["message"])
        mem_hits = sum(1 for l in nearby if "Memory" in l["message"])
        lats     = [l["latency_ms"] for l in nearby]
        rows.append({
            "timestamp":     ts,
            "log_volume":    d["total"],
            "error_rate":    round((d.get("ERROR",0)+d.get("CRITICAL",0))/max(d["total"],1)*100,2),
            "anomaly_count": d.get("anomaly",0),
            "cpu_usage":     min(95, 40+cpu_hits*15+random.randint(0,8)),
            "memory_usage":  min(90, 45+mem_hits*12+random.randint(0,6)),
            "latency_p99":   int(np.percentile(lats,99)) if lats else random.randint(80,400),
            "warn_count":    d.get("WARNING",0),
            "critical_count":d.get("CRITICAL",0),
        })
    return pd.DataFrame(rows).set_index("timestamp")

def generate_anomalies(n=80):
    data  = _get_all()
    anoms = [l for l in data if l["anomaly_score"] >= 0.50]
    sample= sorted(anoms, key=lambda x: x["timestamp"], reverse=True)[:n]
    rows  = []
    for l in sample:
        sev = ("CRITICAL" if l["anomaly_score"]>0.85 else
               "HIGH"     if l["anomaly_score"]>0.70 else "MEDIUM")
        rows.append({
            "timestamp": l["timestamp"],
            "type":      l["message"][:50],
            "service":   l["service"],
            "score":     l["anomaly_score"],
            "severity":  sev,
            "level":     l["level"],
            "resolved":  random.choice([True,True,False]),
            "ttd_min":   random.randint(1,45),
            "ttr_min":   random.randint(5,120),
        })
    return pd.DataFrame(rows)

def get_summary_stats():
    data         = _get_all()
    total        = len(data)
    level_counts = Counter(l["level"] for l in data)
    msg_counts   = Counter(l["message"] for l in data)
    svc_counts   = Counter(l["service"] for l in data)
    anomalies    = [l for l in data if l["anomaly_score"] >= 0.75]
    sec_kw       = ["Unauthorized","Brute force","Failed login","account locked","Rate limit","Suspicious IP"]
    sec_events   = [l for l in data if any(k in l["message"] for k in sec_kw)]
    db_kw        = ["Database","Query","Transaction","disk space"]
    db_events    = [l for l in data if any(k in l["message"] for k in db_kw)]
    return {
        "total":          total,
        "level_counts":   dict(level_counts),
        "top_messages":   msg_counts.most_common(15),
        "svc_counts":     dict(svc_counts),
        "anomaly_count":  len(anomalies),
        "security_count": len(sec_events),
        "db_count":       len(db_events),
        "critical_count": level_counts.get("CRITICAL",0),
        "error_count":    level_counts.get("ERROR",0),
        "warn_count":     level_counts.get("WARNING",0),
    }

def generate_nodes():
    stats = get_summary_stats()
    rng   = np.random.default_rng(42)
    nodes = []
    for i, svc in enumerate(SERVICES):
        angle   = 2*np.pi*i/len(SERVICES)
        tier    = (0 if "gateway" in svc else 1 if "auth" in svc or "collector" in svc else 2)
        r       = [1.5,3.0,4.5][tier]
        svc_vol = stats["svc_counts"].get(svc,10)
        err_cnt = sum(1 for l in _get_all()
                      if l["service"]==svc and l["level"] in ("ERROR","CRITICAL"))
        ratio   = err_cnt/max(svc_vol,1)
        health  = "critical" if ratio>0.25 else ("warn" if ratio>0.12 else "healthy")
        nodes.append({
            "id":     svc,
            "x":      r*np.cos(angle)+rng.uniform(-0.3,0.3),
            "y":      r*np.sin(angle)+rng.uniform(-0.3,0.3),
            "z":      tier*2.0+rng.uniform(-0.4,0.4),
            "tier":   tier,
            "health": health,
            "cpu":    min(95, 30+int(svc_vol/5)),
            "mem":    min(90, 35+int(svc_vol/6)),
            "log_vol":svc_vol,
        })
    return pd.DataFrame(nodes)

def generate_model_metrics():
    epochs = np.arange(1,51)
    rng    = np.random.default_rng(42)
    return pd.DataFrame({
        "epoch":     epochs,
        "train_loss":(1.5*np.exp(-0.08*epochs)+rng.normal(0,0.02,50)).clip(0),
        "val_loss":  (1.6*np.exp(-0.07*epochs)+rng.normal(0,0.03,50)).clip(0),
        "precision": (1-0.8 *np.exp(-0.10*epochs)+rng.normal(0,0.01,50)).clip(0,1),
        "recall":    (1-0.85*np.exp(-0.09*epochs)+rng.normal(0,0.01,50)).clip(0,1),
        "f1":        (1-0.82*np.exp(-0.095*epochs)+rng.normal(0,0.01,50)).clip(0,1),
    })

rng_syn = np.random.default_rng(99)

def _synthetic_logs(n=500):
    MESSAGES = {
        "INFO":  ["Request processed","Connection established","Batch completed"],
        "WARN":  ["High memory usage: 82%","Slow query detected","Retry attempt #3"],
        "ERROR": ["Connection refused","OOMKill detected","Pipeline stage failed"],
        "DEBUG": ["Trace span_id=abc","Feature vector shape: (256, 128)"],
    }
    LEVELS = ["INFO","INFO","INFO","WARN","ERROR","DEBUG"]
    now    = datetime.utcnow()
    out    = []
    for i in range(n):
        ts  = now - timedelta(seconds=(n-i)*random.uniform(0.5,3))
        lvl = random.choice(LEVELS)
        msg = random.choice(MESSAGES[lvl])
        out.append({"timestamp":ts,"level":lvl,"service":random.choice(SERVICES),
                    "message":msg,"anomaly_score":round(float(rng_syn.uniform(0,1)),3),
                    "latency_ms":int(rng_syn.integers(5,2000))})
    return out

def _synthetic_timeseries(hours=24, freq_min=5):
    periods = int(hours*60/freq_min)
    idx = pd.date_range(end=datetime.utcnow(), periods=periods, freq=f"{freq_min}min")
    df  = pd.DataFrame(index=idx)
    df["log_volume"]   = (rng_syn.integers(800,1500,periods)+300*np.sin(np.linspace(0,4*np.pi,periods))).astype(int)
    df["error_rate"]   = rng_syn.uniform(0.5,8,periods).round(2)
    df["anomaly_count"]= rng_syn.integers(0,12,periods)
    df["cpu_usage"]    = (50+20*np.sin(np.linspace(0,6*np.pi,periods))+rng_syn.normal(0,5,periods)).clip(10,95).round(1)
    df["memory_usage"] = (60+15*np.cos(np.linspace(0,4*np.pi,periods))+rng_syn.normal(0,4,periods)).clip(20,95).round(1)
    df["latency_p99"]  = rng_syn.integers(80,400,periods)
    return df
