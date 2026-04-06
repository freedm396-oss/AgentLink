"""
配置模块
提供统一的配置管理
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """配置管理器"""
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path(__file__).parent
        self.configs = {}
        self._load_all()
    
    def _load_all(self):
        """加载所有配置文件"""
        config_files = ['default.yaml', 'patterns.yaml', 'output.yaml']
        
        for config_file in config_files:
            filepath = self.config_dir / config_file
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.configs[config_file.replace('.yaml', '')] = yaml.safe_load(f)
    
    def get(self, key: str, default=None):
        """获取配置值（支持点号分隔）"""
        keys = key.split('.')
        
        # 确定配置文件
        if keys[0] in self.configs:
            config_name = keys[0]
            config_keys = keys[1:]
        else:
            config_name = 'default'
            config_keys = keys
        
        config = self.configs.get(config_name, {})
        
        for k in config_keys:
            if isinstance(config, dict):
                config = config.get(k, default)
            else:
                return default
        
        return config
    
    def update(self, config_name: str, updates: Dict):
        """更新配置"""
        if config_name in self.configs:
            self._deep_update(self.configs[config_name], updates)
    
    def _deep_update(self, target: Dict, source: Dict):
        """深度更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value


# 全局配置实例
config = Config()