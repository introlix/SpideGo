# SpideGo

<div align="center" id="spidego">

**A Search Platform Powered By Searxng But With Features**

[![License](https://img.shields.io/badge/License-GPL%202.0-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-green.svg)](https://fastapi.tiangolo.com/)

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## 🌟 Overview
(This is a side project started by Satyam Mishra.)

SpideGo is a Search platform powered by searxng. Everything including indexing is done by searxng. SpideGo provide extra features on top of it. It provide features such as "Featured Snippets" that shows overview for your result so you don't have to visit every link.

**Note**: Currently SpideGo don't use any LLM for answering anything. But this doesn't mean we won't in future. But it will be optional that user have to enable to use. By default it will be non-llm powered.

---
<div id="roadmap"></div>

### Roadmap (Future Plan)
- **I haven't made any roadmap yet.**
---

<div id="quick-start"></div>

## 🚀 Quick Start
- **Note**: **If you want to use it via docker then go and see release section**

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 22 or higher
- **pnpm**: Package manager for frontend
- **SQLite**: Database for storing workspaces and research data
- **SearXNG**: Self-hosted search engine

### Installation

1. **Clone the repository**

```bash
git clone --recurse-submodules https://github.com/introlix/SpideGo.git
cd SpideGo
```

2. **Install Python dependencies**

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies for backend
cd backend
pip install -e .

# In second terminal
cd searxng/searxng
pip install -e .
```

3. **Install frontend dependencies**

```bash
cd frontend
pnpm install
```

6. **Start the services**

**Terminal 1 - Backend:**
```bash
# From project root
source .venv/bin/activate
uvicorn backend.app:app --reload --port 8889
```

**Terminal 2 - Frontend:**
```bash
cd frontend
pnpm dev
```

**Terminal 3 - Searxng:**
```bash
cd searxng
source server.bash
```

7. **Access the application**

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs


### 🐳 Running with Docker & Docker Compose (Integrated Local Run)

For running the entire application (both Next.js frontend and FastAPI backend) in a single integrated container:

1. **Build the local Docker image**:
   ```bash
   docker build -f Dockerfile.local -t spidego:local .
   ```

3. **Access the application**:
   - Frontend: [http://localhost:8890](http://localhost:8890)
   - Backend API Docs: [http://localhost:8889/docs](http://localhost:8889/docs)
   - Searxng: [http://localhost:8888/docs](http://localhost:8888/docs)


To stop the container, run:
```bash
docker compose down
```

---

## 📝 License

This project is licensed under the GPLv2 - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**[⬆ back to top](#spidego)**

Made with ❤️ by the Satyam Mishra

</div>