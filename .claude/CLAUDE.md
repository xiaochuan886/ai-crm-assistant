# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Business Assistant CRM product - a pluggable, cross-platform AI assistant that integrates with existing CRM systems through natural language conversations. The project is currently in the planning stage with only a PRD document present.

## Product Architecture

Based on the PRD, this will be a multi-component system:

### Core Components
- **AI Widget Frontend**: React + TypeScript + Tailwind CSS
- **Backend API**: FastAPI (Python) with LangChain/LangGraph
- **AI Engine**: OpenAI GPT-4 / Claude 3.5 Sonnet
- **CRM Adapters**: Standardized interfaces for multiple CRM systems (Salesforce, HubSpot, etc.)
- **Database Layer**: PostgreSQL for conversation history, Redis for caching

### Integration Architecture
- **Frontend Integration**: iframe embedding or floating widget in CRM pages
- **Authentication**: Token passing via postMessage API
- **Security**: All CRM API calls happen in user's browser, not on our servers

## Development Phases

### Phase 1 (MVP - 3 months)
- Natural language CRUD operations for customers, orders, tickets
- Fuzzy matching and disambiguation engine
- Business rule validation
- Support for 1-2 major CRM systems

### Phase 2 (Months 4-6)
- Proactive business reminders
- Conversational data analytics
- Support for 3+ CRM systems

### Phase 3 (Future)
- Predictive analytics
- Automated strategy execution

## Technical Implementation Notes

### Key Challenges
1. **Multi-CRM API Diversity**: Adapter pattern to handle different CRM APIs
2. **AI Understanding Accuracy**: Few-shot prompting, tool descriptions optimization
3. **Security**: Token never leaves customer environment
4. **Real-time Communication**: WebSocket for chat interface

### Development Priorities
1. Start with Salesforce adapter as primary CRM system
2. Implement core LangChain Agent with basic CRUD tools
3. Build React widget with secure token handling
4. Create adapter generation framework for scaling to other CRMs

## Project Setup Commands

Since this project doesn't have code yet, these are the anticipated setup commands based on the PRD specifications:

### Frontend (React Widget)
```bash
# Expected setup
npm create vite@latest widget -- --template react-ts
cd widget
npm install
npm install -D tailwindcss
npm install socket.io-client
```

### Backend (FastAPI + LangChain)
```bash
# Expected setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn langchain langchain-openai langgraph redis psycopg2-binary celery
```

### Development
```bash
# Frontend dev server
npm run dev

# Backend dev server
uvicorn main:app --reload

# Redis for caching
redis-server

# Celery worker for async tasks
celery -A app.celery worker --loglevel=info
```

## CRM Integration Requirements

When implementing CRM adapters:
1. Follow the adapter pattern defined in the PRD
2. Each adapter should implement standard interface methods
3. Map CRM-specific fields to standardized internal representations
4. Handle API errors gracefully with user-friendly messages

## AI Agent Development

- Use LangChain Tools for each business operation
- Implement conversation memory for context
- Add validation and confirmation for destructive operations
- Design tools to be composable and reusable

## Security Considerations

- Never store customer CRM tokens on backend servers
- Implement proper CORS and authentication
- Add operation audit logging
- Validate all user inputs and AI-generated instructions