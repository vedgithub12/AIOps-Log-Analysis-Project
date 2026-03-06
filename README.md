# 🧠 AIOps Log Analysis — Streamlit UI v2.0

A production-grade AIOps monitoring dashboard built with Streamlit, Plotly 3D, and scikit-learn.

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/vedgithub12/AIOps-Log-Analysis-Project.git
cd AIOps-Log-Analysis-Project

# 2. Copy UI files into repo (or place this folder inside)
cd aiops-ui

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 📂 Project Structure

```
aiops-ui/
├── app.py                  ← Main entry point + CSS + sidebar nav
├── requirements.txt
├── data/
│   └── generator.py        ← Synthetic data (swap with real pipelines)
└── pages/
    ├── dashboard.py        ← Command Center (KPIs, heatmap, alerts)
    ├── log_explorer.py     ← Search/filter logs + latency violin
    ├── anomaly_detection.py← Score timeline, SHAP, heatmap
    ├── model_analytics.py  ← Training curves, ROC, PR, radar
    ├── infra_3d.py         ← 3D topology, surface, scatter, network
    └── settings.py         ← Pipeline/model/integration config
```

---

## 🎨 Pages

| Page | Description |
|------|-------------|
| 🏠 Dashboard | KPI cards, log volume, error rate, anomaly donut, heatmap, CPU/memory scatter |
| 📋 Log Explorer | Real-time log stream with search, filter, latency violin charts |
| 🔍 Anomaly Detection | Score timeline, SHAP feature importance, type breakdown, active alerts |
| 📊 Model Analytics | Loss curves, confusion matrix, ROC, PR curve, multi-model radar |
| 🌐 Infrastructure 3D | **3D service topology** · **3D anomaly score surface** · **3D CPU/mem/latency scatter** · **3D dependency network** |
| ⚙️ Settings | Kafka/ES/Grafana config, model hyperparameters, alert rules, integrations |

---

## 🔌 Connecting Real Data

Replace functions in `data/generator.py` with your actual data sources:

```python
# Example: pull from Elasticsearch
from elasticsearch import Elasticsearch
es = Elasticsearch("http://localhost:9200")

def generate_logs(n=200):
    resp = es.search(index="logs-*", size=n, sort=[{"@timestamp": "desc"}])
    # parse hits into DataFrame ...
```

---

## 🛠 Tech Stack

- **Streamlit** — UI framework
- **Plotly** — Interactive 2D & 3D charts  
- **scikit-learn** — IsolationForest, One-Class SVM
- **Kafka** — Log ingestion
- **Elasticsearch** — Log storage & search
- **Prometheus + Grafana** — Metrics

---

Built with ❤️ · github.com/vedgithub12/AIOps-Log-Analysis-Project
