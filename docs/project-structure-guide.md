# PROJECT-STRUCTURE-GUIDE.md

This file provides guidance to AI Code Assistant when working with code in this repository.

## Project Overview

BrainBeaver is a LLM-based knowledge management tool that processes websites and markdown documents to create an interactive knowledge network. It combines React frontend with FastAPI backend, using force-directed graph visualization to show relationships between knowledge concepts.

## Development Commands

### Frontend Development (Node.ViteUI)
```bash
cd src/Node.ViteUI/
npm run dev      # Start development server (port 5173)
npm run build    # Build for production
npm run preview  # Preview production build
```

### Backend Development (Python FastAPI)
```bash
cd src/Python.FastAPI/
uv run app.py    # Run backend server (port 8111)
# Or with uvicorn:
uvicorn app:app --host 0.0.0.0 --port 8111 --reload
```

### Docker Development
```bash
cd docker/
docker compose up -d    # Start all services
docker compose down     # Stop all services
```

### Testing
No automated test suite is currently configured. Manual testing through API docs at http://localhost:8112/docs

## Architecture

### Backend Structure
- **Modular Design**: Each domain (concepts, networks, references, extract) follows handler → service → repository → model pattern
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Message Queue**: RabbitMQ for async processing
- **LLM Integration**: Supports both OpenAI API and local Ollama models with routing system

### Frontend Structure  
- **React 19 + TypeScript** with Vite build system
- **3D Visualization**: Uses `@cosmograph/cosmos` for force-directed graph rendering
- **Data Flow**: Fetches knowledge network data and renders interactive 3D visualization with selection capabilities

### Key Services
- **Extract Module**: Processes websites/markdown into knowledge chunks
- **LLM Processing**: Summarizes content, generates keywords, creates relationships
- **Network Generation**: Builds connections between knowledge concepts
- **Visualization**: Renders interactive 3D knowledge graph

## Configuration

### Required Setup
1. Copy `secret.sample.properties` to `secret.properties`
2. Configure Naver Search API credentials (CLIENT_ID, CLIENT_SECRET) 
3. Optionally configure OpenAI API key (can use Ollama instead)

### Service Ports
- Frontend: 5173
- Backend API: 8112  
- Database: 5432
- PgAdmin: 5050
- RabbitMQ: 5672, 15672
- Portainer: 9000

## Important Notes

- **CORS Configuration**: Backend allows localhost:5173 and Docker network access
- **Database Migrations**: SQLAlchemy handles schema creation automatically
- **LLM Routing**: System can fallback between OpenAI and Ollama based on availability
- **Docker Volumes**: Persistent data stored in `docker/volumes/` directory
- **Backup System**: Jenkins service handles automated backups to `backup/` directory
