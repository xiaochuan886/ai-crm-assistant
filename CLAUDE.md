# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Business Assistant CRM product - a pluggable, cross-platform AI assistant that integrates with existing CRM systems through natural language conversations. The project implements a complete architecture with core AI engine, CRM adapters, and React frontend.

## Architecture Principles

### Core Design
- **AI Engine CRM Separation**: Core AI logic in `core/` is completely independent of CRM-specific code
- **Standardized Interface**: All CRM systems implement `BaseCrmAdapter` from `adapters/base_adapter.py`
- **Adapter Pattern**: Each CRM system has its own adapter (e.g., `odoo_adapter.py`)
- **Configuration-Driven**: New CRM systems supported through adapter implementation, not core code changes

### Key Components
- **Core AI Engine** (`core/`): LangChain-based agent with natural language processing
- **CRM Adapters** (`adapters/`): Pluggable adapters for different CRM systems
- **Frontend Widget** (`frontend/`): React + TypeScript + Tailwind CSS chat interface
- **FastAPI Server** (`main.py`): WebSocket server for real-time communication

## Development Commands

### Backend (Python)
```bash
# Run development server
python main.py

# Run specific test files
python tests/test_simple.py
python tests/test_architecture.py
python tests/test_odoo_enhanced.py

# Test Odoo connection
python test_odoo_connection.py

# Test AI integration
python test_ai_service.py
python test_openai_integration.py
python test_deepseek_integration.py

# Debug enhanced adapter
python debug_enhanced_adapter.py
```

### Frontend (React + TypeScript)
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview build
npm run preview

# Lint code
npm run lint
```

### Testing
```bash
# Run architecture validation tests
python tests/test_architecture_quick.py

# Test specific components
python test_simple_adapter.py
python test_ai_assistant.py

# Full integration test
python test_complete.py
```

## Code Architecture

### Core AI Engine (`core/`)
- **`agent.py`**: Main AI agent with LangChain integration, natural language processing, and conversation management
- **`ai_services/`**: AI service provider integrations (OpenAI, DeepSeek, Claude)
- **Tools**: Standardized CRM operations exposed to AI as tools

### CRM Adapters (`adapters/`)
- **`base_adapter.py`**: Abstract base class defining standard CRM interface
- **`odoo_adapter.py`**: Odoo JSON-RPC implementation
- **`odoo_adapter_enhanced.py`**: Extended Odoo adapter with advanced features
- **`mock_adapter.py`**: Mock adapter for testing

### Standardized Data Structures
```python
@dataclass
class CustomerData:
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class OperationResult:
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_details: Optional[str] = None
```

### Frontend Structure (`frontend/src/`)
- **`components/`**: React components (ChatInterface, MessageList, MessageBubble, etc.)
- **`hooks/`**: Custom React hooks (useChatMessages, useWebSocket)
- **`services/`**: API and WebSocket service layers
- **`types/`**: TypeScript type definitions

## Key Implementation Details

### AI Agent Workflow
1. Natural language input received via WebSocket or REST API
2. Intent parsing using AI service (OpenAI/DeepSeek/Claude)
3. Context management for multi-turn conversations
4. CRM operation execution through adapter interface
5. Response formatting and delivery

### Adapter Implementation Pattern
1. Inherit from `BaseCrmAdapter`
2. Implement all abstract methods (`create_customer`, `search_customers`, etc.)
3. Handle CRM-specific API calls and data transformation
4. Return standardized `OperationResult` objects

### Frontend Integration
- WebSocket connection to `main.py` for real-time chat
- React Query for data fetching and caching
- Tailwind CSS for styling
- TypeScript for type safety

## Configuration

### CRM Adapter Configuration
```python
# Odoo Adapter
odoo_config = {
    'url': 'https://your-odoo-instance.com',
    'db': 'your_database',
    'username': 'your_username',
    'password': 'your_password'
}

# AI Service Configuration
ai_config = {
    'provider': 'openai',  # or 'deepseek', 'claude'
    'api_key': 'your-api-key',
    'model': 'gpt-4',
    'temperature': 0.1
}
```

### Frontend Configuration
- Vite proxy configuration in `vite.config.ts` routes `/api` to backend
- Tailwind CSS configuration in `tailwind.config.js`
- TypeScript configuration in `tsconfig.json`

## Development Guidelines

### Adding New CRM Adapters
1. Create new adapter class inheriting from `BaseCrmAdapter`
2. Implement all required abstract methods
3. Handle CRM-specific authentication and API calls
4. Add test cases in `tests/` directory
5. Update documentation

### Core AI Engine Modifications
- Keep CRM-agnostic - no CRM-specific imports in `core/`
- Use adapter interface for all CRM operations
- Maintain conversation context for multi-turn dialogues
- Handle errors gracefully with user-friendly messages

### Frontend Development
- Components are organized by function (chat, messages, input)
- Use TypeScript hooks for state management
- WebSocket integration handled in `hooks/useWebSocket.ts`
- API calls in `services/api.ts`

## Common Development Tasks

### Testing AI Integration
```bash
# Test with mock adapter
python tests/test_simple.py

# Test with real AI service
python test_openai_integration.py

# Test full agent workflow
python test_ai_assistant.py
```

### Testing CRM Adapters
```bash
# Test Odoo connection
python test_odoo_connection.py

# Test enhanced adapter features
python tests/test_odoo_enhanced.py

# Debug adapter issues
python debug_enhanced_adapter.py
```

### Frontend Development
```bash
cd frontend
npm run dev  # Starts dev server on port 3000
# Backend should run on port 8000 for WebSocket connection
```

## Architecture Validation

The project includes architecture validation tests that ensure:
- Core AI engine remains independent of CRM implementations
- Adapters correctly implement the standard interface
- No circular dependencies between core and adapter code

Run validation with:
```bash
python tests/test_architecture_quick.py
```

## Security Considerations

- CRM credentials (passwords, API keys) should be stored securely
- WebSocket connections use appropriate CORS configuration
- Input validation on both frontend and backend
- Error messages don't expose sensitive system information