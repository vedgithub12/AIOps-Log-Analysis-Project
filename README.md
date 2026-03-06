# 🧠 AIOps Log Analysis & Anomaly Detection Platform

> An end-to-end **AI-powered log monitoring system** that ingests, analyzes, and visualizes system logs in real time — deployed on **AWS EC2** with IAM-based security, featuring ML-driven anomaly detection and an interactive **Streamlit dashboard with 3D visualizations**.

## Project Demo

Click here to watch the project demo:  
[DEMO](https://drive.google.com/file/d/154h9px3MIKkvF2ZDSJzdPOrwSDzejQSW/view?usp=sharing)

---

## 📌 Table of Contents

- [What This Project Does](#what-this-project-does)
- [Live Demo Screenshots](#live-demo-screenshots)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [AWS Setup (EC2 + IAM)](#aws-setup-ec2--iam)
- [Project Structure](#project-structure)
- [Installation & Running Locally](#installation--running-locally)
- [Deploying on AWS EC2](#deploying-on-aws-ec2)
- [Dashboard Pages](#dashboard-pages)
- [How Anomaly Detection Works](#how-anomaly-detection-works)
- [Real Log Analysis Results](#real-log-analysis-results)
- [Contributing](#contributing)

---

## What This Project Does

Modern systems generate thousands of log lines every second. Manually reading them is impossible. This project solves that by:

1. **Ingesting** raw system logs (from files, Kafka, or live streams)
2. **Parsing & categorizing** each log line into services automatically
3. **Scoring anomalies** using ML models (IsolationForest, AutoEncoder LSTM)
4. **Alerting** when critical patterns are detected (brute force, DB failures, CPU spikes)
5. **Visualizing everything** in a beautiful real-time dashboard — including **3D infrastructure topology**

### Key Problems It Solves

| Problem | How This Project Helps |
|---|---|
| Too many logs to read manually | Auto-classifies and scores every event |
| Hard to spot patterns across services | Heatmaps and timelines across all services |
| Security threats go unnoticed | Dedicated security event detection & alerting |
| Slow incident response | Anomaly alerts with time-to-detect tracking |
| No visibility into infrastructure health | 3D topology map with live health status |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS EC2 Instance                          │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  Log Sources  │───▶│  Log Parser  │───▶│  ML Anomaly       │   │
│  │  (files/      │    │  + Service   │    │  Detection        │   │
│  │   Kafka/API)  │    │  Categorizer │    │  (IsolationForest)│   │
│  └──────────────┘    └──────────────┘    └────────┬─────────┘   │
│                                                    │              │
│  ┌─────────────────────────────────────────────────▼──────────┐  │
│  │              Streamlit Dashboard (port 8501)                │  │
│  │  • Command Center   • Log Explorer   • Anomaly Detection    │  │
│  │  • Model Analytics  • 3D Infrastructure  • Settings         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Security: IAM Role attached to EC2 · IAM User for CLI access    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Category | Technology |
|---|---|
| **Language** | Python 3.12 |
| **Dashboard UI** | Streamlit |
| **Visualizations** | Plotly (2D + 3D interactive charts) |
| **ML / Anomaly Detection** | scikit-learn (IsolationForest, One-Class SVM) |
| **Data Processing** | Pandas, NumPy |
| **Log Ingestion** | Apache Kafka (optional), file-based parser |
| **Monitoring** | Prometheus + Grafana (optional) |
| **Cloud** | AWS EC2 (Ubuntu 24.04) |
| **Security** | AWS IAM (User + Role) |
| **Containerization** | Docker (optional) |

---

## AWS Setup (EC2 + IAM)

This project runs on **AWS EC2** and uses **IAM** for secure access. Here's exactly how it's set up.

### Step 1 — Create an IAM User (for CLI / deployment access)

1. Go to **AWS Console → IAM → Users → Create User**
2. Name it something like `aiops-deploy-user`
3. Attach the following permissions:
   - `AmazonEC2FullAccess` — to manage the EC2 instance
   - `AmazonS3ReadOnlyAccess` — to read log files from S3 (if applicable)
   - `CloudWatchLogsReadOnlyAccess` — to pull CloudWatch logs (optional)
4. Under **Security credentials**, create an **Access Key** (choose CLI type)
5. Save the `Access Key ID` and `Secret Access Key` — you'll need these for `aws configure`

> ⚠️ Never commit your AWS credentials to GitHub. Use environment variables or AWS Secrets Manager.

### Step 2 — Create an IAM Role (for EC2 instance permissions)

1. Go to **IAM → Roles → Create Role**
2. Choose **AWS Service → EC2** as the trusted entity
3. Attach these policies:
   - `CloudWatchLogsFullAccess` — so the app can write logs to CloudWatch
   - `AmazonS3ReadOnlyAccess` — to read log files stored in S3
   - `AmazonSSMFullAccess` — for Systems Manager access (optional but recommended)
4. Name the role `aiops-ec2-role`
5. **Attach the role to your EC2 instance:**
   - EC2 Console → Select your instance → Actions → Security → Modify IAM Role → Select `aiops-ec2-role`

### Step 3 — Launch an EC2 Instance

| Setting | Recommended Value |
|---|---|
| **AMI** | Ubuntu Server 24.04 LTS |
| **Instance Type** | `t2.medium` (2 vCPU, 4GB RAM) or larger |
| **Storage** | 20 GB GP3 SSD |
| **Security Group** | See below |
| **IAM Role** | `aiops-ec2-role` (created above) |
| **Key Pair** | Create and download a `.pem` key |

### Step 4 — Configure Security Group (Firewall / Open Ports)

| Port | Protocol | Source | Purpose |
|---|---|---|---|
| `22` | TCP | Your IP | SSH access |
| `8501` | TCP | `0.0.0.0/0` | Streamlit dashboard |
| `9090` | TCP | Your IP | Prometheus (optional) |
| `3000` | TCP | Your IP | Grafana (optional) |

To open port 8501 via CLI:
```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0
```

---

## Project Structure

```
ALOPS_project/
│
├── app.py                        # 🚀 Main Streamlit entry point
├── requirements.txt              # Python dependencies
├── README.md                     # This file
│
├── data/
│   ├── system_logs.txt           # 📄 Real log file (1,000 events analyzed)
│   └── generator.py             # Log parser + synthetic data fallback
│
└── pages/
    ├── dashboard.py             # 🏠 Command Center — KPIs, charts, alerts
    ├── log_explorer.py          # 📋 Search & filter log stream
    ├── anomaly_detection.py     # 🔍 ML scores, SHAP features, timeline
    ├── model_analytics.py       # 📊 ROC, confusion matrix, training curves
    ├── infra_3d.py              # 🌐 3D topology, surface, scatter plots
    └── settings.py              # ⚙️  Pipeline & model configuration
```

---

## Installation & Running Locally

### Prerequisites

- Python 3.10 or higher
- pip

### 1. Clone the repository

```bash
git clone https://github.com/vedgithub12/ALOPS_project.git
cd ALOPS_project
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501** 🎉

---

## Deploying on AWS EC2

### Connect to your EC2 instance

```bash
chmod 400 your-key.pem
ssh -i "your-key.pem" ubuntu@<YOUR_EC2_PUBLIC_IP>
```

### Set up the environment on EC2

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python & pip
sudo apt install python3-pip python3-venv git -y

# Clone the project
git clone https://github.com/vedgithub12/ALOPS_project.git
cd ALOPS_project

# Create virtual environment and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the dashboard (accessible from the internet)

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Access it at: **http://\<YOUR_EC2_PUBLIC_IP\>:8501**

### Keep it running after you disconnect (using screen)

```bash
# Install screen
sudo apt install screen -y

# Start a named session
screen -S aiops

# Run the app inside screen
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Detach from screen (app keeps running): Press Ctrl+A then D
# Re-attach later:
screen -r aiops
```

### Or run as a background service (systemd)

```bash
sudo nano /etc/systemd/system/aiops.service
```

Paste this:

```ini
[Unit]
Description=AIOps Streamlit Dashboard
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/ALOPS_project
ExecStart=/home/ubuntu/ALOPS_project/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable aiops
sudo systemctl start aiops

# Check status
sudo systemctl status aiops
```

---

## Dashboard Pages

### 🏠 Command Center (Dashboard)
The main overview page. Shows:
- **KPI cards** — total events, CRITICAL count, ERROR count, security alerts, anomaly count
- **Log volume over time** — per-minute time series with error rate overlay
- **Severity distribution** — donut chart (INFO / WARNING / ERROR / CRITICAL)
- **Volume by service** — which service is generating the most logs
- **Security events heatmap** — brute force, failed logins, unauthorized access over time
- **Top anomaly alerts table** — most recent high-score events

### 📋 Log Explorer
Search and filter through all log events. Shows:
- Full-text keyword search across all 1,000+ log messages
- Filter by log level (INFO / WARNING / ERROR / CRITICAL)
- Filter by service (api-gateway, auth-service, db-proxy, etc.)
- Anomaly score distribution histogram
- Color-coded live log stream with real timestamps

### 🔍 Anomaly Detection
The core ML analysis page. Shows:
- Adjustable score threshold slider
- **Score timeline** — every event plotted by time and anomaly score
- **Feature importance** (SHAP-style) — which signals contribute most to anomaly scores
- **Anomaly count by service** — which services have the most issues
- **Severity level timeline** — CRITICAL/WARNING/anomaly counts per minute
- Active unresolved alerts table

### 📊 Model Analytics
ML model performance metrics. Shows:
- Training & validation loss curves over 50 epochs
- Precision / Recall / F1 score progression
- Confusion matrix (true positives, false positives, etc.)
- ROC curve with AUC score
- Precision-Recall curve
- Multi-model radar comparison (IsolationForest vs LSTM vs SVM)

### 🌐 Infrastructure 3D
Four interactive 3D views — drag to rotate, scroll to zoom:
- **Service Topology** — 3D graph of all services colored by health status (green/amber/red)
- **Anomaly Score Surface** — 3D surface showing anomaly intensity across services and time
- **CPU × Memory × Latency Scatter** — every observation as a 3D bubble
- **Dependency Network** — force-directed 3D graph of service dependencies

### ⚙️ Settings
Configure the pipeline without touching code:
- Kafka bootstrap servers, topic, batch size
- Elasticsearch host and index pattern
- Alert thresholds and notification channels (Slack, PagerDuty, Email)
- ML model hyperparameters (n_estimators, contamination, learning rate)
- Integration status (Kafka, Grafana, Prometheus, S3, etc.)

---

## How Anomaly Detection Works

Each log line is assigned an **anomaly score from 0.0 to 1.0** based on two factors:

**1. Base score from log level:**

| Log Level | Base Score |
|---|---|
| INFO | 0.10 |
| WARNING | 0.50 |
| ERROR | 0.75 |
| CRITICAL | 0.95 |

**2. Extra boost from message content:**

| Condition | Score Boost |
|---|---|
| CPU usage at 95% | +0.15 |
| Transaction rollback / deadlock | +0.10 |
| Database connection failed | +0.10 |
| Brute force / account locked | +0.10 |
| Unhandled exception in payment | +0.10 |
| Memory usage exceeded threshold | +0.10 |
| High I/O wait time | +0.08 |
| Service health check failed | +0.05 |

Events with a score ≥ 0.75 are flagged as **anomalies**. The threshold is adjustable in the dashboard.

---

## Real Log Analysis Results

Analysis of the included `system_logs.txt` (1,000 events, 2026-01-27):

| Metric | Count |
|---|---|
| Total log events | **1,000** |
| CRITICAL events | **49** |
| ERROR events | **102** |
| WARNING events | **152** |
| INFO events | 697 |
| Anomalies detected (score ≥ 0.75) | **151** |
| Security-related events | **194** |
| Database-related events | **202** |

**Top threats identified:**
- `Transaction rollback due to deadlock` — 35 occurrences
- `Database disk space low` — 41 occurrences
- `Unauthorized access attempt to admin panel` — 37 occurrences
- `Rate limit exceeded for user` — 37 occurrences
- `Brute force protection activated` — 34 occurrences
- `Multiple failed login attempts, account locked` — 34 occurrences
- `High I/O wait time on primary disk` — 37 occurrences

**Most affected services:**
- `log-collector` — 227 events
- `auth-service` — 222 events (highest security risk)
- `db-proxy` — 202 events (highest DB risk)
- `api-gateway` — 198 events

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and test locally
4. Commit: `git commit -m "Add: my feature description"`
5. Push: `git push origin feature/my-feature`
6. Open a Pull Request

---

## License

This project is open source. Feel free to use, modify, and share.

---

*Built by [@vedgithub12](https://github.com/vedgithub12) · Deployed on AWS EC2 · Powered by Python + Streamlit + Plotly*
