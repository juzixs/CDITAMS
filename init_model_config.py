import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cditams.settings')
django.setup()

from apps.settings.models import SystemConfig


def init_model_config():
    print("初始化模型配置...")
    configs = [
        # 模型设置
        {'config_key': 'llm_enabled', 'config_value': 'false', 'value_type': 'boolean', 'config_group': 'model', 'description': '启用大语言模型', 'sort': 1},
        {'config_key': 'llm_api_base', 'config_value': 'https://api.xiaomimimo.com/v1', 'value_type': 'string', 'config_group': 'model', 'description': 'API 基础地址 (base_url)', 'sort': 2},
        {'config_key': 'llm_api_key', 'config_value': '', 'value_type': 'string', 'config_group': 'model', 'description': 'API Key', 'sort': 3},
        {'config_key': 'llm_model_name', 'config_value': 'mimo-v2-pro', 'value_type': 'string', 'config_group': 'model', 'description': '模型名称 (model)', 'sort': 4},
        {'config_key': 'llm_temperature', 'config_value': '1.0', 'value_type': 'string', 'config_group': 'model', 'description': '温度 (temperature) 取值范围 0~2', 'sort': 5},
        {'config_key': 'llm_top_p', 'config_value': '0.95', 'value_type': 'string', 'config_group': 'model', 'description': '核采样 (top_p) 取值范围 0~1', 'sort': 6},
        {'config_key': 'llm_max_tokens', 'config_value': '4096', 'value_type': 'int', 'config_group': 'model', 'description': '最大生成长度 (max_completion_tokens)', 'sort': 7},
        {'config_key': 'llm_frequency_penalty', 'config_value': '0', 'value_type': 'string', 'config_group': 'model', 'description': '频率惩罚 (frequency_penalty) 取值范围 -2~2', 'sort': 8},
        {'config_key': 'llm_presence_penalty', 'config_value': '0', 'value_type': 'string', 'config_group': 'model', 'description': '存在惩罚 (presence_penalty) 取值范围 -2~2', 'sort': 9},
        {'config_key': 'llm_stream', 'config_value': 'false', 'value_type': 'boolean', 'config_group': 'model', 'description': '流式输出 (stream)', 'sort': 10},
    ]
    
    for c in configs:
        obj, created = SystemConfig.objects.update_or_create(config_key=c['config_key'], defaults=c)
        action = "创建" if created else "更新"
        print(f"  {action}: {c['description']} ({c['config_key']})")
    
    print(f"模型配置初始化完成，共 {len(configs)} 项配置")


if __name__ == '__main__':
    init_model_config()