import json
import os
import base64
import uuid
from openai import OpenAI


# ==================== 两步图片识别提示词 ====================

STEP1_PROMPT_ALL = """请仔细观察这张图片，逐行识别图片中的内容。

要求：
1. 先识别图片中有哪些列/字段（如资产编号、卡片编号、设备名称、型号、数量等），不要预设字段名，根据图片实际内容判断
2. 按行整理每行的内容，列出你识别到的所有字段及其对应值
3. 如果某行内容模糊或缺失，请注明
4. 资产编号通常类似 XACD-XXX-XXX-XXX 格式，请重点关注

输出格式示例：
[行1] 字段1: 值, 字段2: 值, ...
[行2] 字段1: 值, 字段2: 值, ..."""

STEP1_PROMPT_CHECKED = """请仔细观察这张图片，这是一个"人工勾选"的场景。

要求：
1. 先识别图片中有哪些列/字段，不要预设字段名，根据图片实际内容判断
2. 仔细辨别哪些行被人工勾选、标记
3. 仅整理被勾选/标记的行的内容，忽略未被勾选的行
4. 如果某行内容模糊或缺失，请注明

输出格式示例：
[被勾选-行1] 字段1: 值, 字段2: 值, ...
[被勾选-行2] 字段1: 值, 字段2: 值, ..."""

STEP2_PROMPT_TEMPLATE = """请将以下设备资产识别结果整理为严格的JSON格式。

输出格式：
{{
  "asset_numbers": ["资产编号1", "资产编号2"],
  "card_numbers": ["卡片编号1", "卡片编号2"]
}}

规则：
1. 只返回纯JSON，不要有任何解释文字、不要用markdown代码块
2. 从识别结果中找出所有资产编号，放入 asset_numbers 数组
3. 从识别结果中找出所有卡片编号，放入 card_numbers 数组
4. 如果某类编号为空，用空数组 []
5. 如果识别结果中包含合并写法的资产编号（如 XACD-Z-001-001-001/002/003），需要拆解为独立编号，每个编号单独放入数组
6. 连号写法（如 006~009）也需要拆解为独立编号
7. 编号格式保持原文，不要修改前缀或格式

识别结果：
{result}"""


# ==================== 配置读取 ====================

def get_llm_config():
    """从数据库获取所有LLM配置，每次调用都重新读取以确保获取最新配置"""
    from .models import SystemConfig

    config_keys = [
        'llm_enabled', 'llm_api_key', 'llm_api_base', 'llm_model_name',
        'llm_temperature', 'llm_top_p', 'llm_max_tokens',
        'llm_frequency_penalty', 'llm_presence_penalty', 'llm_stream',
    ]
    configs = {}
    for key in config_keys:
        try:
            obj = SystemConfig.objects.get(config_key=key)
            value = obj.config_value
            if obj.value_type == 'int':
                configs[key] = int(value) if value else None
            elif obj.value_type == 'boolean':
                configs[key] = value.lower() in ('true', '1', 'yes') if value else False
            else:
                configs[key] = value if value else None
        except SystemConfig.DoesNotExist:
            configs[key] = None

    return {
        'enabled': configs.get('llm_enabled', False) or False,
        'api_key': configs.get('llm_api_key') or '',
        'api_base': configs.get('llm_api_base') or 'https://api.xiaomimimo.com/v1',
        'model_name': configs.get('llm_model_name') or 'mimo-v2-pro',
        'temperature': float(configs.get('llm_temperature') or 0.1),
        'top_p': float(configs.get('llm_top_p') or 0.95),
        'max_tokens': int(configs.get('llm_max_tokens') or 4096),
        'frequency_penalty': float(configs.get('llm_frequency_penalty') or 0),
        'presence_penalty': float(configs.get('llm_presence_penalty') or 0),
        'stream': configs.get('llm_stream', False) or False,
    }


def is_llm_enabled():
    """检查LLM是否启用（llm_enabled=True 且 api_key非空）"""
    config = get_llm_config()
    return config['enabled'] and bool(config['api_key'])


def _get_client(config):
    """根据配置创建OpenAI客户端"""
    return OpenAI(api_key=config['api_key'], base_url=config['api_base'])


def _build_params(config, messages, max_tokens=None):
    """构建API调用参数"""
    params = {
        'model': config['model_name'],
        'messages': messages,
        'temperature': config['temperature'],
        'top_p': config['top_p'],
        'max_completion_tokens': max_tokens or config['max_tokens'],
        'frequency_penalty': config['frequency_penalty'],
        'presence_penalty': config['presence_penalty'],
        'stream': config['stream'],
    }
    return params


def _format_messages_for_log(messages):
    """将messages格式化为日志字符串，图片只记录类型和大小，不记录base64数据"""
    parts = []
    for msg in messages:
        role = msg.get('role', '?')
        content = msg.get('content', '')
        if isinstance(content, str):
            parts.append(f"[{role}] {content[:200]}{'...' if len(content) > 200 else ''}")
        elif isinstance(content, list):
            for item in content:
                if item.get('type') == 'text':
                    text = item.get('text', '')
                    parts.append(f"[{role} text] {text[:150]}{'...' if len(text) > 150 else ''}")
                elif item.get('type') == 'image_url':
                    url = item.get('image_url', {}).get('url', '')
                    if url.startswith('data:'):
                        parts.append(f"[{role} image] data URI, 长度: {len(url)} chars")
                    else:
                        parts.append(f"[{role} image] URL: {url}")
    return '\n'.join(parts)


# ==================== 核心调用函数 ====================

def call_llm(messages, max_tokens=None, log_callback=None):
    """非流式文本聊天调用，使用数据库中的所有LLM配置参数。
    每次调用都重新读取数据库配置，确保设置页面修改后立即生效。

    Args:
        messages: OpenAI messages 列表
        max_tokens: 可选，覆盖数据库中的max_tokens配置
        log_callback: 可选，日志回调函数，接收(str)消息

    Returns:
        str: AI返回的文本内容

    Raises:
        RuntimeError: LLM未启用
        Exception: API调用失败
    """
    config = get_llm_config()
    if not config['enabled'] or not config['api_key']:
        raise RuntimeError('LLM未启用或未配置API Key，请在系统设置-模型设置中配置')

    if log_callback:
        log_callback(f"[发送消息] {_format_messages_for_log(messages)}")

    client = _get_client(config)
    params = _build_params(config, messages, max_tokens)
    params['stream'] = False

    response = client.chat.completions.create(**params)
    content = response.choices[0].message.content
    finish_reason = response.choices[0].finish_reason if response.choices else 'unknown'

    # fallback: 推理模型（如 mimo-v2-omni）的 content 可能为空，取 reasoning_content
    if not content or not content.strip():
        reasoning = getattr(response.choices[0].message, 'reasoning_content', None)
        if reasoning and reasoning.strip():
            content = reasoning.strip()
            if log_callback:
                log_callback("[提示] content为空，使用reasoning_content作为结果")

    if log_callback:
        usage = getattr(response, 'usage', None)
        usage_str = ''
        if usage:
            usage_str = f', prompt_tokens={usage.prompt_tokens}, completion_tokens={usage.completion_tokens}, total_tokens={usage.total_tokens}'
        log_callback(f"[模型返回] finish_reason={finish_reason}{usage_str}")
        if finish_reason == 'length':
            log_callback("[警告] 输出被token限制截断，建议在系统设置中增大 max_completion_tokens")
        if content:
            log_callback(f"[模型返回内容] {content[:500]}{'...' if len(content) > 500 else ''}")
        else:
            log_callback(f"[模型返回内容] (空)")

    return content


def call_llm_stream(messages, max_tokens=None):
    """流式文本聊天调用，使用数据库中的所有LLM配置参数。
    每次调用都重新读取数据库配置，确保设置页面修改后立即生效。

    Args:
        messages: OpenAI messages 列表
        max_tokens: 可选，覆盖数据库中的max_tokens配置

    Yields:
        str: AI返回的文本内容片段（delta）

    Raises:
        RuntimeError: LLM未启用
        Exception: API调用失败
    """
    config = get_llm_config()
    if not config['enabled'] or not config['api_key']:
        raise RuntimeError('LLM未启用或未配置API Key，请在系统设置-模型设置中配置')

    client = _get_client(config)
    params = _build_params(config, messages, max_tokens)
    params['stream'] = True

    stream = client.chat.completions.create(**params)
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def call_llm_auto(messages, max_tokens=None):
    """根据数据库中的 llm_stream 配置自动选择流式或非流式调用。"""
    config = get_llm_config()
    if not config['enabled'] or not config['api_key']:
        raise RuntimeError('LLM未启用或未配置API Key，请在系统设置-模型设置中配置')

    if config['stream']:
        full_content = []
        for chunk in call_llm_stream(messages, max_tokens):
            full_content.append(chunk)
        return ''.join(full_content)
    else:
        return call_llm(messages, max_tokens)


def call_llm_vision(messages, max_tokens=None, log_callback=None):
    """非流式视觉/图片理解调用，使用数据库中的所有LLM配置参数。
    每次调用都重新读取数据库配置，确保设置页面修改后立即生效。

    Args:
        messages: OpenAI messages 列表（包含image_url类型的多模态消息）
        max_tokens: 可选，覆盖数据库中的max_tokens配置
        log_callback: 可选，日志回调函数，接收(str)消息

    Returns:
        str: AI返回的文本内容

    Raises:
        RuntimeError: LLM未启用
        Exception: API调用失败
    """
    return call_llm(messages, max_tokens, log_callback=log_callback)


def call_llm_vision_stream(messages, max_tokens=None):
    """流式视觉/图片理解调用，使用数据库中的所有LLM配置参数。"""
    yield from call_llm_stream(messages, max_tokens)


def call_llm_vision_auto(messages, max_tokens=None):
    """根据数据库中的 llm_stream 配置自动选择流式或非流式视觉调用。"""
    return call_llm_auto(messages, max_tokens)


# ==================== 两步图片识别 ====================

def _compress_image(image_bytes, max_width=2048, quality=85):
    """压缩图片，保持可读性的同时减小体积"""
    from PIL import Image
    import io as _io

    img = Image.open(_io.BytesIO(image_bytes))
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = _io.BytesIO()
    fmt = 'PNG' if image_bytes[:8] == b'\x89PNG\r\n\x1a\n' else 'JPEG'
    if fmt == 'JPEG':
        img = img.convert('RGB')
        img.save(buf, format='JPEG', quality=quality)
    else:
        img.save(buf, format='PNG')
    return buf.getvalue()


def call_llm_vision_two_step(image_bytes, log_callback=None, base_url=None, parse_photo_only=False, image_input_method='http_url'):
    """两步AI图片识别：
    第一步：发送图片给AI，让其自由识别图中所有字段和内容
    第二步：将第一步文本结果发给AI，整理为规范JSON

    Args:
        image_bytes: 图片二进制数据
        log_callback: 日志回调函数，接收(str)消息
        base_url: 服务器应用URL（如 https://itams.chidafeiji.com），用于构造图片HTTP URL
        parse_photo_only: True=人工勾选模式（仅识别被标记行），False=识别全部行
        image_input_method: 'http_url' 或 'base64'，图片传入方式

    Returns:
        str: JSON字符串，格式为 {"asset_numbers": [...], "card_numbers": [...]}

    Raises:
        RuntimeError: LLM未启用
        Exception: API调用失败
    """
    from django.conf import settings as django_settings

    if not base_url:
        base_url = 'http://127.0.0.1:8000'

    temp_file_path = None

    try:
        # 压缩图片（6MB大图 → ~200-500KB）
        original_size = len(image_bytes)
        compressed = _compress_image(image_bytes)
        if log_callback:
            log_callback(f"[图片] 压缩: {original_size} bytes → {len(compressed)} bytes")

        # 检测图片格式
        if compressed[:8] == b'\x89PNG\r\n\x1a\n':
            file_ext = 'png'
            mime_type = 'image/png'
        else:
            file_ext = 'jpg'
            mime_type = 'image/jpeg'

        # 构造图片传入方式
        if image_input_method == 'base64':
            # base64 data URI 方式
            b64_data = base64.b64encode(compressed).decode('utf-8')
            image_url = f"data:{mime_type};base64,{b64_data}"
            if log_callback:
                log_callback(f"[图片] 使用base64 data URI传入，大小: {len(b64_data)} chars")
        else:
            # HTTP URL 方式（默认）
            if 'localhost' in base_url or '127.0.0.1' in base_url:
                if log_callback:
                    log_callback(f"[警告] app_url 配置为本地地址({base_url})，AI API可能无法访问图片URL。"
                                 f"请在系统设置中配置外网可达的应用URL")

            temp_name = f"img_{uuid.uuid4().hex}.{file_ext}"
            temp_dir = os.path.join(django_settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, temp_name)
            with open(temp_file_path, 'wb') as f:
                f.write(compressed)

            image_url = f"{base_url.rstrip('/')}/media/temp/{temp_name}"
            if log_callback:
                log_callback(f"[图片] 保存到临时文件: temp/{temp_name}，使用HTTP URL传入")
                log_callback(f"[图片] URL: {image_url}")

        # 第一步：图片识别
        if parse_photo_only:
            step1_prompt = STEP1_PROMPT_CHECKED
            if log_callback:
                log_callback("[第一步] 模式: 人工勾选 - 仅识别被标记的行")
        else:
            step1_prompt = STEP1_PROMPT_ALL
            if log_callback:
                log_callback("[第一步] 模式: 全量识别 - 识别图片中所有行")

        step1_messages = [
            {"role": "system", "content": "你是一个专业的图像内容识别助手，擅长从照片中识别表格、列表和文本信息。"},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": step1_prompt}
            ]}
        ]

        step1_result = call_llm_vision(step1_messages, log_callback=log_callback)

        # 第一步完成后立即清理临时文件（第二步不需要图片）
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                if log_callback:
                    log_callback("[清理] 临时图片文件已删除")
            except OSError:
                pass
            temp_file_path = None

        if not step1_result or not step1_result.strip():
            raise RuntimeError('第一步图片识别返回内容为空')

        if log_callback:
            log_callback(f"[第一步] 识别完成，返回内容长度: {len(step1_result)} 字符")

        # 第二步：整理为JSON
        step2_prompt = STEP2_PROMPT_TEMPLATE.format(result=step1_result)
        step2_messages = [
            {"role": "system", "content": "你是一个专业的数据整理助手，擅长将文本识别结果整理为规范的JSON格式。"},
            {"role": "user", "content": step2_prompt}
        ]

        step2_result = call_llm(step2_messages, log_callback=log_callback)

        if not step2_result or not step2_result.strip():
            raise RuntimeError('第二步JSON整理返回内容为空')

        if log_callback:
            log_callback(f"[第二步] JSON整理完成，返回内容长度: {len(step2_result)} 字符")

        return step2_result

    finally:
        # 兜底清理（正常流程已在第一步后清理）
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass
