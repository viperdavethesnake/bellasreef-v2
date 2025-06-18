# Bella's Reef Backend

**A modular backend system for intelligent reef tank automation.** Built with Python, FastAPI, and PostgreSQL, this API-driven application supports real-time monitoring, lighting behaviors, smart outlet control, and hardware integration with Raspberry Pi.

---

## ✨ Features

- **FastAPI backend** with modular routing and JWT-based auth
- **PostgreSQL** database for config and historical sensor data
- **PWM lighting control** (Native Pi GPIO + PCA9685)
- **Advanced lighting behaviors**:
  - Daylight, lunar, moonlight, and weather-based cycles
  - Location-aware simulation (e.g., mimic Bora Bora lighting)
  - User-triggered cloudburst, storms, lightning
- **Smart outlet integration** (VeSync cloud, Shelly, Kasa local)
- **Polling engine** for sensors and probe logging
- **Scheduler** for lights, pumps, and automated tasks
- **Alerting and triggers** based on defined conditions
- **System health** monitoring and centralized system manager

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Raspberry Pi (for hardware integration)
- Optional: Docker, I2C-enabled PCA board

### Installation

Clone the repo:

```bash
git clone https://github.com/your-username/bellasreef-backend.git
cd bellasreef-backend
```

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Setup database:

```bash
alembic upgrade head
```

Run the app:

```bash
uvicorn app.main:app --reload
```

---

## 📝 Project Structure

```
app/
├── api/                # API routes
├── core/               # Auth, system manager, scheduler
├── db/                 # Models, schemas, DB logic
├── hardware/           # PWM, outlets, sensors
├── services/           # Polling, triggers, lighting behaviors
├── main.py             # FastAPI app startup
```

---

## 🌐 API Usage

Interactive API docs will be available at:

```
http://localhost:8000/docs
```

---

## ⚖️ License

MIT License

---

## ❤️ Contributing

Pull requests welcome! For major changes, please open an issue first.

For questions, ideas, or help: [**David**](mailto\:your-email@example.com)

