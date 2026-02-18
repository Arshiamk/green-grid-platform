# Green Grid Platform 🟢✨

> **Intelligent Energy Management & Analytics**

Green Grid is a high-performance energy analytics platform designed for real-time monitoring, billing, and forecasting. It features a premium, modern dashboard with a focus on visual excellence and actionable insights.

## ✨ Key Features

- **Premium UI/UX**: Built with React, Tailwind CSS, and Framer Motion. Features Glassmorphism, Jakarta Sans typography, and smooth micro-animations.
- **Smart Analytics**: Real-time consumption tracking with interactive Recharts visualizations.
- **Robust Infrastructure**: Fully Dockerized stack including Django (Backend), React (Frontend), Redis, Postgres, and Celery.
- **Command Center**: Enhanced Django Admin powered by Jazzmin for powerful infrastructure management.
- **Automated Billing**: Cycle-based billing engine with status tracking and PDF generation (stubbed).

## 🚀 Quick Start (Docker)

The easiest way to run the platform is using Docker Compose:

```bash
# 1. Clone & Enter
git clone https://github.com/Arshiamk/green-grid-platform.git
cd green-grid-platform

# 2. Build & Start
docker-compose up --build -d
```

Access the platform:

- **Frontend Portal**: [http://localhost](http://localhost)
- **Command Center (Admin)**: [http://localhost/admin](http://localhost/admin)

## 🛠️ Tech Stack

### Frontend

- **Framework**: Vite + React + TypeScript
- **Styling**: Tailwind CSS (Emerald Theme)
- **UI Components**: Shadcn UI + Lucide Icons
- **Motion**: Framer Motion
- **Charts**: Recharts

### Backend

- **Core**: Django 5.x + Django REST Framework
- **Auth**: SimpleJWT (Bearer Authentication)
- **Worker**: Celery + Redis
- **Database**: PostgreSQL 16
- **Admin**: Django-Jazzmin

## 📦 Project Structure

```text
green-grid-platform/
├── src/               # Django Backend Implementation
├── frontend/          # React Frontend Implementation
├── scripts/           # Deployment & Dev scripts
├── docker-compose.yml # Full Stack Orchestration
├── .env.example       # Template for environment variables
└── README.md          # This documentation
```

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

Developed by **Arshiamk** | 2026
