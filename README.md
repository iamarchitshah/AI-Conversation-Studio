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

# 📸 Screenshots

Add screenshots here.

```
screenshots/
    home.png
    chat.png
    history.png
```

Example:

```markdown
![Home](screenshots/home.png)

![Chat](screenshots/chat.png)
```

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
