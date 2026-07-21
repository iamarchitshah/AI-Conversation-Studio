# 🤖 AI Conversation Studio

> A modern AI-powered conversation platform built with **FastAPI**, **SQLite**, and a clean web interface. Create, manage, and interact with AI conversations through a fast, responsive, and easy-to-use application.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?style=for-the-badge&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

---

# 📌 Overview

AI Conversation Studio is a lightweight yet powerful conversational AI platform designed to provide a seamless chatting experience.

The project combines a **FastAPI backend**, **SQLite database**, and an intuitive frontend into a single application, allowing developers to quickly run, test, and extend AI chat functionality without complex setup.

The entire application is served from one FastAPI server, making deployment simple and efficient.

---

## Run it (3 steps)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000
```

# ✨ Features

- 💬 AI-powered conversation interface
- ⚡ FastAPI backend
- 🗄 SQLite database integration
- 🎨 Clean and responsive UI
- 📜 Conversation history management
- 🔄 RESTful API architecture
- 🚀 Single-server deployment
- 📱 Mobile-friendly interface
- 🔒 Modular backend structure
- 🛠 Easy to customize and extend

---

# 🏗 Project Structure

```
AI-Conversation-Studio/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── routes/
│   ├── static/
│   ├── templates/
│   ├── requirements.txt
│   └── ...
│
├── README.md
└── LICENSE
```

---

# 🛠 Tech Stack

### Backend
- Python
- FastAPI
- SQLite
- Uvicorn

### Frontend
- HTML5
- CSS3
- JavaScript

### Database
- SQLite

---

# ⚙ Installation

## 1. Clone Repository

```bash
git clone https://github.com/iamarchitshah/AI-Conversation-Studio.git

cd AI-Conversation-Studio/backend
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Run Server

```bash
uvicorn main:app --port 8000
```

---

## 4. Open Browser

Visit

```
http://localhost:8000
```

That's it!

No separate frontend server required.

---

# ☁️ Deploy to AWS EKS (Kubernetes)

Deploy AI Conversation Studio to Amazon EKS with persistent SQLite storage via EBS volumes.

## Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) installed & configured (`aws configure`)
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- [Docker](https://docs.docker.com/get-docker/) installed
- An [AWS account](https://aws.amazon.com/) with sufficient permissions

## Step 1 — Create EKS Cluster

If you don't have an EKS cluster yet, create one using `eksctl`:

```bash
eksctl create cluster \
  --name ai-conversation-studio \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 4 \
  --managed
```

> ⏱ This takes ~15 minutes. While it runs, proceed to Step 2 in parallel.

## Step 2 — Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name ai-conversation-studio \
  --region us-east-1
```

## Step 3 — Build & Push Docker Image

```bash
chmod +x scripts/build-and-push.sh
scripts/build-and-push.sh <YOUR_AWS_ACCOUNT_ID> us-east-1
```

**Example:** `scripts/build-and-push.sh 123456789012 us-east-1`

## Step 4 — Update Deployment Image

Edit `k8s/deployment.yaml` and replace `<YOUR_AWS_ACCOUNT_ID>` and `<REGION>` with your actual values:

```yaml
image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/ai-conversation-studio:latest
```

## Step 5 — Deploy to EKS

```bash
kubectl config use-context <your-eks-cluster-context>
chmod +x scripts/deploy-eks.sh
scripts/deploy-eks.sh <YOUR_AWS_ACCOUNT_ID> us-east-1
```

Or manually apply all manifests:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/service.yaml
```

## Step 6 — Verify

```bash
# Check pods
kubectl get pods -n ai-conversation-studio

# Get the LoadBalancer URL
kubectl get svc -n ai-conversation-studio ai-conversation-studio-service \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

Open the returned URL in your browser — you should see the AI Conversation Studio UI.

## Kubernetes Architecture

| Resource | Description |
|----------|-------------|
| `Namespace` | Isolated namespace `ai-conversation-studio` |
| `Deployment` | 2 replicas (auto-scales 2–10), with health probes |
| `Service` | AWS LoadBalancer (port 80 → container 8000) |
| `PVC` | 1Gi EBS `gp3` volume for SQLite persistence |
| `ConfigMap` | App configuration (`DB_PATH`, etc.) |
| `HPA` | Auto-scale on CPU (70%) and memory (80%) |

## Important Notes

- **Data Persistence:** SQLite database is stored on a PVC backed by AWS EBS (`gp3`). Data survives pod restarts but is **tied to a single AZ**. For multi-AZ HA, migrate to Amazon RDS (PostgreSQL).
- **No Rolling Updates Data Loss:** Because SQLite is a file-based DB, rolling updates work fine — the new pod mounts the same PVC.
- **Backup**: Periodically backup the PVC. Example:
  ```bash
  kubectl exec -n ai-conversation-studio deployment/ai-conversation-studio -- \
    sh -c "cp /data/studio.db /data/studio-$(date +%Y%m%d).db"
  ```

---

# 🚀 API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | / | Home Page |
| GET | /docs | Swagger Documentation |
| POST | /chat | AI Conversation |
| GET | /history | Conversation History |
| POST | /conversation | Create Conversation |
| DELETE | /conversation/{id} | Delete Conversation |

> Endpoints may vary depending on your implementation.

---


---

# 📦 Dependencies

- FastAPI
- Uvicorn
- SQLite
- Pydantic
- Python 3.10+

Install with

```bash
pip install -r requirements.txt
```

---

# 💡 Future Improvements

- User Authentication
- Multiple AI Models
- Dark Mode
- File Upload Support
- Voice Input
- Streaming Responses
- Export Conversations
- Markdown Rendering
- Docker Support
- Cloud Deployment

---

# 🧪 Development

Run with auto reload

```bash
uvicorn main:app --reload
```

---

# 📖 API Documentation

FastAPI automatically generates documentation.

Swagger UI

```
http://localhost:8000/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository

2. Create a feature branch

```bash
git checkout -b feature/NewFeature
```

3. Commit changes

```bash
git commit -m "Added New Feature"
```

4. Push branch

```bash
git push origin feature/NewFeature
```

5. Open a Pull Request

---

# ⭐ Support

If you found this project useful,

⭐ Star this repository

🍴 Fork it

🛠 Contribute to it

---

# 👨‍💻 Author

**Archit Shah**

GitHub:
https://github.com/iamarchitshah

---

## ❤️ Thank You

Thank you for visiting this project.

If you like it, don't forget to leave a ⭐ on GitHub!
