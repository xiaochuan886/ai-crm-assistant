"""
配置管理器 - 支持多种CRM系统的可插拔配置
支持 INI、YAML、JSON 格式的配置文件
"""

import os
import configparser
import json
import yaml
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CRMConfig:
    """CRM系统配置"""
    crm_type: str  # 'odoo', 'salesforce', 'hubspot', etc.
    url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    timeout: int = 30
    enable_caching: bool = True

@dataclass
class AIServiceConfig:
    """AI服务配置"""
    provider: str  # 'deepseek', 'openai', 'claude', 'mock'
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 2000

@dataclass
class AppConfig:
    """应用程序配置"""
    crm: CRMConfig
    ai_service: AIServiceConfig
    logging_level: str = "INFO"
    debug_mode: bool = False
    custom_field_mapping: Dict[str, Any] = None
    business_rules: Dict[str, Any] = None
    # 对话上下文配置，例如历史轮数
    conversation: Dict[str, Any] = None

class ConfigManager:
    """配置管理器 - 支持可插拔CRM配置"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，如果为None则自动检测
        """
        self.config_path = config_path or self._find_config_file()
        self.config: Optional[AppConfig] = None

    def _find_config_file(self) -> str:
        """自动查找配置文件"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'configs')

        # 按优先级查找配置文件
        search_paths = [
            os.path.join(config_dir, 'app_config.yaml'),
            os.path.join(config_dir, 'app_config.yml'),
            os.path.join(config_dir, 'config.yaml'),
            os.path.join(config_dir, 'config.yml'),
            os.path.join(config_dir, 'odoo_config.yaml'),
            os.path.join(config_dir, 'odoo_config.yml'),
            os.path.join(config_dir, 'config.ini'),
            os.path.join(config_dir, 'odoo_config.ini'),
        ]

        for path in search_paths:
            if os.path.exists(path):
                logger.info(f"找到配置文件: {path}")
                return path

        # 如果没有找到配置文件，返回默认路径
        default_path = os.path.join(config_dir, 'odoo_config.yaml')
        logger.warning(f"未找到配置文件，使用默认路径: {default_path}")
        return default_path

    def load_config(self) -> AppConfig:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        file_ext = os.path.splitext(self.config_path)[1].lower()

        try:
            if file_ext in ['.yaml', '.yml']:
                raw_config = self._load_yaml_config()
            elif file_ext == '.ini':
                raw_config = self._load_ini_config()
            elif file_ext == '.json':
                raw_config = self._load_json_config()
            else:
                raise ValueError(f"不支持的配置文件格式: {file_ext}")

            self.config = self._parse_config(raw_config)
            logger.info(f"成功加载配置文件: {self.config_path}")
            return self.config

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise

    def _load_yaml_config(self) -> Dict[str, Any]:
        """加载YAML配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_ini_config(self) -> Dict[str, Any]:
        """加载INI配置文件"""
        config = configparser.ConfigParser()
        config.read(self.config_path, encoding='utf-8')

        # 转换为字典格式
        result = {}
        for section in config.sections():
            result[section] = dict(config.items(section))

        return result

    def _load_json_config(self) -> Dict[str, Any]:
        """加载JSON配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _parse_config(self, raw_config: Dict[str, Any]) -> AppConfig:
        """解析配置字典为配置对象"""

        # 解析CRM配置
        crm_config = self._parse_crm_config(raw_config)

        # 解析AI服务配置
        ai_config = self._parse_ai_config(raw_config)

        # 解析应用配置
        app_config = AppConfig(
            crm=crm_config,
            ai_service=ai_config,
            logging_level=raw_config.get('logging', {}).get('level', 'INFO'),
            debug_mode=raw_config.get('environment', {}).get('development', {}).get('debug_mode', False),
            custom_field_mapping=raw_config.get('custom_field_mapping', {}),
            business_rules=raw_config.get('business_rules', {}),
            conversation=raw_config.get('conversation', {})
        )

        return app_config

    def _parse_crm_config(self, raw_config: Dict[str, Any]) -> CRMConfig:
        """解析CRM配置"""
        # 支持不同的配置结构
        if 'odoo' in raw_config:
            crm_data = raw_config['odoo']
            crm_type = 'odoo'
        elif 'salesforce' in raw_config:
            crm_data = raw_config['salesforce']
            crm_type = 'salesforce'
        elif 'hubspot' in raw_config:
            crm_data = raw_config['hubspot']
            crm_type = 'hubspot'
        elif 'crm' in raw_config:
            crm_data = raw_config['crm']
            crm_type = crm_data.get('type', 'odoo')  # 默认为odoo
        else:
            # 尝试从顶层配置中获取
            crm_type = raw_config.get('crm_type', 'odoo')
            crm_data = raw_config

        return CRMConfig(
            crm_type=crm_type,
            url=crm_data.get('url', 'http://localhost:8069'),
            api_key=crm_data.get('api_key'),
            username=crm_data.get('username'),
            password=crm_data.get('password'),
            database=crm_data.get('db_name') or crm_data.get('database'),
            db_host=crm_data.get('db_host'),
            db_port=crm_data.get('db_port'),
            db_user=crm_data.get('db_user'),
            db_password=crm_data.get('db_password'),
            timeout=crm_data.get('timeout', 30),
            enable_caching=crm_data.get('enable_caching', True)
        )

    def _parse_ai_config(self, raw_config: Dict[str, Any]) -> AIServiceConfig:
        """解析AI服务配置"""
        if 'ai_service' in raw_config:
            ai_data = raw_config['ai_service']
        elif 'ai' in raw_config:
            ai_data = raw_config['ai']
        else:
            # 默认配置
            ai_data = {
                'provider': 'mock',
                'model': 'mock-model',
                'api_key': None,
                'temperature': 0.1,
                'max_tokens': 2000
            }

        return AIServiceConfig(
            provider=ai_data.get('provider', 'mock'),
            model=ai_data.get('model', 'mock-model'),
            api_key=ai_data.get('api_key'),
            base_url=ai_data.get('base_url'),
            temperature=ai_data.get('temperature', 0.1),
            max_tokens=ai_data.get('max_tokens', 2000)
        )

    def get_crm_adapter_class(self):
        """根据配置获取CRM适配器类"""
        crm_type = self.config.crm.crm_type.lower()

        if crm_type == 'odoo':
            from adapters.odoo_adapter_enhanced import EnhancedOdooAdapter
            return EnhancedOdooAdapter
        elif crm_type == 'salesforce':
            # from adapters.salesforce_adapter import SalesforceAdapter
            # return SalesforceAdapter
            raise NotImplementedError("Salesforce adapter not implemented yet")
        elif crm_type == 'hubspot':
            # from adapters.hubspot_adapter import HubspotAdapter
            # return HubspotAdapter
            raise NotImplementedError("HubSpot adapter not implemented yet")
        else:
            # 默认使用mock适配器
            from adapters.mock_adapter import MockCrmAdapter
            return MockCrmAdapter

    def get_ai_service_class(self):
        """根据配置获取AI服务类"""
        provider = self.config.ai_service.provider.lower()

        # DeepSeek现在使用OpenAI兼容模式，配置中provider设为openai
        if provider == 'openai':
            from core.ai_services.openai_service import OpenAIService
            return OpenAIService
        elif provider == 'claude':
            # from core.ai_services.claude_service import ClaudeService
            # return ClaudeService
            raise NotImplementedError("Claude service not implemented yet")
        elif provider == 'mock':
            from core.ai_services.mock_ai_service import MockAIService
            return MockAIService
        else:
            # 默认使用mock
            from core.ai_services.mock_ai_service import MockAIService
            return MockAIService

    def create_crm_adapter(self):
        """创建CRM适配器实例"""
        adapter_class = self.get_crm_adapter_class()

        # 将CRMConfig转换为字典格式传递给适配器
        crm_config_dict = {
            'crm_type': self.config.crm.crm_type,
            'url': self.config.crm.url,
            'api_key': self.config.crm.api_key,
            'username': self.config.crm.username,
            'password': self.config.crm.password,
            'database': self.config.crm.database,
            'db': self.config.crm.database,  # 为EnhancedOdooAdapter添加db字段
            'db_host': self.config.crm.db_host,
            'db_port': self.config.crm.db_port,
            'db_user': self.config.crm.db_user,
            'db_password': self.config.crm.db_password,
            'db_name': self.config.crm.database,  # 为EnhancedOdooAdapter添加db_name字段
            'timeout': self.config.crm.timeout,
            'enable_caching': self.config.crm.enable_caching,
            'custom_field_mapping': self.config.custom_field_mapping or {},
            'business_rules': self.config.business_rules or {}
        }

        return adapter_class(crm_config_dict)

    def create_ai_service(self):
        """创建AI服务实例"""
        service_class = self.get_ai_service_class()

        # 将AIServiceConfig转换为字典格式传递给AI服务
        ai_config_dict = {
            'provider': self.config.ai_service.provider,
            'model': self.config.ai_service.model,
            'api_key': self.config.ai_service.api_key,
            'base_url': self.config.ai_service.base_url,
            'temperature': self.config.ai_service.temperature,
            'max_tokens': self.config.ai_service.max_tokens
        }

        return service_class(ai_config_dict)

    def validate_config(self) -> bool:
        """验证配置是否有效"""
        try:
            # 验证CRM配置
            crm = self.config.crm
            if not crm.url:
                logger.error("CRM URL不能为空")
                return False

            if crm.crm_type in ['odoo'] and not (crm.username and crm.password):
                logger.error("Odoo需要用户名和密码")
                return False

            # 验证AI服务配置
            ai = self.config.ai_service
            if not ai.provider:
                logger.error("AI服务提供者不能为空")
                return False

            if not ai.model:
                logger.error("AI模型不能为空")
                return False

            logger.info("配置验证通过")
            return True

        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False