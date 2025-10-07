"""
AI CRM助手 - FastAPI WebSocket服务器
支持实时聊天和CRM操作的主服务器
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging
import os
from pydantic import BaseModel

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from core.fallback_ai_agent import FallbackAiAgent
from core.langchain_agent import LangChainAgent
from core.agent import ConversationContext
from core.config_manager import ConfigManager
from adapters.mock_adapter import MockCrmAdapter

def initialize_config_manager():
    """初始化配置管理器"""
    try:
        # 使用新的AI配置文件
        config_file = "/Users/lujunfeng/workspace/ai-crm-assistant/configs/ai_config.yaml"
        config_manager = ConfigManager(config_file)
        app_config = config_manager.load_config()

        # 验证配置
        if not config_manager.validate_config():
            logger.error("配置验证失败")
            raise ValueError("配置验证失败")

        logger.info(f"成功加载配置，CRM类型: {app_config.crm.crm_type}, AI提供者: {app_config.ai_service.provider}")
        return config_manager, app_config

    except Exception as e:
        logger.error(f"初始化配置管理器失败: {e}")
        # 使用默认配置作为回退
        logger.info("使用默认配置作为回退")
        config_manager = ConfigManager()
        app_config = config_manager.load_config()
        return config_manager, app_config

# 全局变量存储连接和会话
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.sessions: Dict[str, Dict] = {}
        self.conversation_contexts: Dict[str, ConversationContext] = {}  # 新增：存储会话上下文

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)

    async def broadcast(self, message: dict):
        for session_id in self.active_connections:
            await self.send_message(session_id, message)
    
    def get_or_create_context(self, session_id: str, user_id: str = "default") -> ConversationContext:
        """获取或创建会话上下文"""
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                history=[],
                chat_history=[],
                session_data={}
            )
        return self.conversation_contexts[session_id]

# 初始化配置管理器和适配器
try:
    # 使用新的配置管理器
    config_manager, app_config = initialize_config_manager()

    # 创建CRM适配器
    crm_adapter = config_manager.create_crm_adapter()
    logger.info(f"使用CRM适配器: {type(crm_adapter).__name__}")

    # 创建AI服务
    ai_service = config_manager.create_ai_service()
    logger.info(f"使用AI服务: {type(ai_service).__name__}")

    # 为FallbackAiAgent准备AI配置
    ai_config = {
        "provider": app_config.ai_service.provider,
        "model": app_config.ai_service.model,
        "api_key": app_config.ai_service.api_key,
        "base_url": app_config.ai_service.base_url,
        "temperature": app_config.ai_service.temperature,
        "max_tokens": app_config.ai_service.max_tokens,
        "timeout": getattr(app_config.ai_service, 'timeout', 30),
        "retry_attempts": getattr(app_config.ai_service, 'retry_attempts', 2),
        # 会话记忆窗口配置，从YAML读取
        "conversation": app_config.conversation or {"history_rounds": 5},
        "fallback": {
            "provider": "mock",
            "enable_on_failure": True,
            "retry_after_failures": 3
        }
    }

except Exception as e:
    logger.error(f"初始化配置管理器失败: {e}")
    logger.info("回退到Mock适配器和默认AI配置")
    crm_adapter = MockCrmAdapter({})

    # 使用默认AI配置
    ai_config = {
        "provider": "mock",
        "model": "mock-model",
        "api_key": None,
        "base_url": None,
        "temperature": 0.1,
        "max_tokens": 2000,
        "fallback": {
            "provider": "mock",
            "enable_on_failure": False
        }
    }

manager = ConnectionManager()
assistant = FallbackAiAgent(crm_adapter, ai_config)
langchain_agent = LangChainAgent()  # 新增：LangChain智能体
logger.info("使用支持回退的AI Agent")
logger.info(f"AI服务状态: {assistant.get_service_status()}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    logger.info("AI CRM助手服务器启动")
    yield
    # 关闭时清理
    logger.info("AI CRM助手服务器关闭")

# 创建FastAPI应用
app = FastAPI(
    title="AI CRM助手 API",
    description="智能CRM助手API服务器，支持WebSocket实时通信",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "ai-crm-assistant"
    }

# API状态
@app.get("/api/status")
async def get_api_status():
    return {
        "status": "running",
        "active_connections": len(manager.active_connections),
        "active_sessions": len(manager.sessions),
        "timestamp": datetime.now().isoformat()
    }

# 会话管理
@app.post("/api/sessions/create")
async def create_session(user_id: Optional[str] = None):
    session_id = str(uuid.uuid4())

    # 创建会话记录
    session_info = {
        "session_id": session_id,
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "message_count": 0
    }

    manager.sessions[session_id] = session_info
    logger.info(f"Created new session: {session_id}")

    return {"session_id": session_id}

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id not in manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return manager.sessions[session_id]

class ChatMessage(BaseModel):
    session_id: str
    message: str

# 聊天消息发送
@app.post("/api/chat/message")
async def send_chat_message(item: ChatMessage):
    if item.session_id not in manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # 使用AI助手处理消息
        response = await assistant.process_request(item.message, item.session_id, "default_user")

        # 更新会话活动
        manager.sessions[item.session_id]["last_activity"] = datetime.now().isoformat()
        manager.sessions[item.session_id]["message_count"] += 1

        return {
            "response": response,
            "session_id": item.session_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

# 获取聊天历史
@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    if session_id not in manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # 这里应该从数据库获取历史记录
    # 暂时返回空列表
    return []

# WebSocket端点
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            logger.info(f"Received WebSocket message: {message_data}")

            # 处理不同类型的消息
            if message_data.get("type") == "message":
                # 用户消息
                await handle_user_message(session_id, message_data.get("data", {}).get("content", ""))

            elif message_data.get("type") == "typing":
                # 打字状态
                await handle_typing_status(session_id, message_data.get("data", {}).get("is_typing", False))

            elif message_data.get("type") == "join_session":
                # 加入会话
                await handle_join_session(session_id)

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected: {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)

async def handle_user_message(session_id: str, content: str):
    """处理用户消息 - 使用LangChain智能体"""
    try:
        # 获取或创建会话上下文
        context = manager.get_or_create_context(session_id)
        
        # 发送用户消息确认
        await manager.send_message(session_id, {
            "type": "user_message",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "data": {"content": content}
        })

        # 发送打字状态
        await manager.send_message(session_id, {
            "type": "typing",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "data": {"isTyping": True}
        })

        try:
            # 初始化LangChain智能体（如果尚未初始化）
            if not langchain_agent.is_initialized():
                langchain_agent.initialize(crm_adapter, context)
            
            # 使用LangChain智能体处理消息
            response = await langchain_agent.process_message(content)
            
            # 发送打字状态结束
            await manager.send_message(session_id, {
                "type": "typing",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "data": {"isTyping": False}
            })

            # 发送AI响应
            await manager.send_message(session_id, {
                "type": "ai_response",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "data": {"content": response}
            })
            
        except Exception as langchain_error:
            logger.warning(f"LangChain智能体处理失败，回退到原有AI助手: {langchain_error}")
            
            # 回退到原有AI助手
            response = await assistant.process_request(content, session_id, "default_user")
            
            # 发送打字状态结束
            await manager.send_message(session_id, {
                "type": "typing",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "data": {"isTyping": False}
            })

            # 发送AI响应
            await manager.send_message(session_id, {
                "type": "ai_response",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "data": {"content": response.get('message', '抱歉，我无法处理您的请求。')}
            })

        # 更新会话活动
        if session_id in manager.sessions:
            manager.sessions[session_id]["last_activity"] = datetime.now().isoformat()
            manager.sessions[session_id]["message_count"] += 1

    except Exception as e:
        logger.error(f"处理用户消息时发生错误: {e}")
        
        # 发送错误响应
        await manager.send_message(session_id, {
            "type": "ai_response",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "data": {"content": "抱歉，处理您的请求时发生了错误，请稍后重试。"}
        })

async def handle_typing_status(session_id: str, is_typing: bool):
    """处理打字状态"""
    # 这里可以向其他用户广播打字状态（如果是群聊）
    logger.info(f"Session {session_id} typing: {is_typing}")

async def handle_join_session(session_id: str):
    """处理加入会话"""
    if session_id not in manager.sessions:
        # 创建新会话
        manager.sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0
        }

    # 发送欢迎消息
    await manager.send_message(session_id, {
        "type": "status_update",
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "data": {"status": "connected", "message": "已连接到AI助手"}
    })

# CRM操作API
@app.post("/api/crm/customer")
async def create_customer(customer_data: dict):
    """创建客户"""
    try:
        # 这里应该使用CRM适配器
        # 暂时返回模拟数据
        return {
            "success": True,
            "customer_id": str(uuid.uuid4()),
            "message": "客户创建成功"
        }
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail="Failed to create customer")

@app.get("/api/crm/customers/search")
async def search_customers(q: str):
    """搜索客户"""
    try:
        # 这里应该使用CRM适配器
        # 暂时返回空列表
        return []
    except Exception as e:
        logger.error(f"Error searching customers: {e}")
        raise HTTPException(status_code=500, detail="Failed to search customers")

@app.post("/api/crm/lead")
async def create_lead(lead_data: dict):
    """创建销售线索"""
    try:
        # 这里应该使用CRM适配器
        # 暂时返回模拟数据
        return {
            "success": True,
            "lead_id": str(uuid.uuid4()),
            "message": "销售线索创建成功"
        }
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail="Failed to create lead")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)