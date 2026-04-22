import json
import os
import urllib.request
import urllib.error
from dotenv import load_dotenv
import sys
import time
from datetime import datetime

# 加载项目根目录下的 .env 文件
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# 从环境变量中读取配置
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# 定义日志保存路径
LOG_DIR = "D:\\chat-log"
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

# --- 1. 定义本地文件操作功能 (Tools) ---

def list_files(directory="."):
    """列出目录下所有文件及其基本属性"""
    try:
        if not os.path.isdir(directory):
            return f"错误: {directory} 不是一个有效的目录。"
        files_info = []
        for entry in os.scandir(directory):
            stats = entry.stat()
            files_info.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size": stats.st_size,
                "mtime": time.ctime(stats.st_mtime)
            })
        return json.dumps(files_info, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"列出文件失败: {str(e)}"

def rename_file(old_path, new_path):
    """重命名文件或目录"""
    try:
        os.rename(old_path, new_path)
        return f"成功: 已将 {old_path} 重命名为 {new_path}"
    except Exception as e:
        return f"重命名失败: {str(e)}"

def delete_file(file_path):
    """删除文件"""
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            return f"成功: 已删除文件 {file_path}"
        else:
            return f"错误: {file_path} 不是文件或不存在。"
    except Exception as e:
        return f"删除失败: {str(e)}"

def create_file(file_path, content=""):
    """新建文件并写入内容"""
    try:
        # 确保父目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功: 已创建文件 {file_path}"
    except Exception as e:
        return f"创建文件失败: {str(e)}"

def read_file(file_path):
    """读取文件内容"""
    try:
        if not os.path.exists(file_path):
            return f"错误: 文件 {file_path} 不存在。"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"读取文件失败: {str(e)}"

def fetch_web_content(url):
    """访问网页并返回其内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"获取网页内容失败: {str(e)}"

def search_chat_log(query):
    """查找聊天历史记录"""
    print(f"\n系统日志: 正在搜索历史日志，查询内容: '{query}'...")
    log_content = read_file(LOG_FILE)
    if log_content.startswith("错误:"):
        return f"暂无历史记录可供查找 (日志文件不存在)。"
    
    # 构造请求，让 LLM 根据日志内容回答查询
    prompt = f"以下是历史聊天的关键信息记录：\n\n{log_content}\n\n请根据以上信息，回答用户的查找请求：'{query}'。如果日志中没有相关信息，请明确说明。"
    
    messages = [{"role": "user", "content": prompt}]
    response = call_llm(messages, stream=False, use_tools=False)
    
    if response and 'choices' in response:
        return response['choices'][0]['message']['content']
    return "查找历史记录失败，请稍后重试。"

# --- 2. 映射工具函数 ---
AVAILABLE_TOOLS = {
    "list_files": list_files,
    "rename_file": rename_file,
    "delete_file": delete_file,
    "create_file": create_file,
    "read_file": read_file,
    "fetch_web_content": fetch_web_content,
    "search_chat_log": search_chat_log
}

# --- 3. 定义工具描述 (OpenAI Tools Schema) ---
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出指定目录下的文件及信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "目录路径，默认为当前目录 '.'"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rename_file",
            "description": "修改文件或目录的名称",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_path": {"type": "string", "description": "原始路径"},
                    "new_path": {"type": "string", "description": "新路径"}
                },
                "required": ["old_path", "new_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "删除指定的文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要删除的文件路径"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "在指定路径创建新文件并写入内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件保存路径"},
                    "content": {"type": "string", "description": "要写入的文件内容"}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取并返回指定文件的内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要读取的文件路径"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_web_content",
            "description": "通过 URL 实时访问并抓取网页 HTML 内容。当用户提出需要联网、查看网址、获取新闻或实时信息时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "要访问的完整 URL (包含 http/https)"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_chat_log",
            "description": "当用户想要查找之前的聊天历史、回忆过去的对话内容、或者询问过去发生了什么时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "用户的查找请求描述"}
                },
                "required": ["query"]
            }
        }
    }
]

# --- 4. 核心逻辑：带工具调用的聊天循环 ---

def call_llm(messages, stream=False, use_tools=True):
    """封装 API 请求逻辑，支持流式和非流式"""
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 创建副本，避免原地修改原始消息列表
    msgs_copy = [msg.copy() for msg in messages]
    
    # 确保 messages 列表中至少有一个 user 消息，以兼容某些本地模型模板
    has_user_msg = any(msg.get('role') == 'user' for msg in msgs_copy)
    if not has_user_msg:
        if msgs_copy and msgs_copy[0].get('role') == 'system':
            msgs_copy.insert(1, {"role": "user", "content": "(系统初始化对话)"})
        else:
            msgs_copy.insert(0, {"role": "user", "content": "(系统初始化对话)"})

    payload = {
        "model": MODEL,
        "messages": msgs_copy,
        "stream": stream
    }
    if use_tools:
        payload["tools"] = TOOLS_SCHEMA
        payload["tool_choice"] = "auto"
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers=headers, 
        method='POST'
    )
    
    try:
        if not stream:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        else:
            return urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        print(f"API 错误: {e.code}")
        print(e.read().decode('utf-8'))
        return None
    except Exception as e:
        print(f"网络错误: {str(e)}")
        return None

def extract_5w_info(messages):
    """提取最近对话的 5W 关键信息并保存"""
    # 获取最后 5 次用户和助手的对话（约 10 条消息）
    recent_msgs = messages[-10:] if len(messages) > 10 else messages
    chat_content = ""
    for msg in recent_msgs:
        if msg['role'] in ['user', 'assistant']:
            chat_content += f"{msg['role']}: {msg.get('content', '')}\n"

    prompt = (
        "请从以下对话中提取关键信息，并严格按照 5W 规则格式化输出：\n"
        "- 谁 (Who)\n"
        "- 做了什么事 (What)\n"
        "- 什么时候 (When)\n"
        "- 在何处 (Where)\n"
        "- 为什么要做这件事 (Why)\n\n"
        "注意：如果 When, Where, Why 没有明确信息，请留空。只需输出提取后的内容，不要有其他解释。\n\n"
        f"对话内容：\n{chat_content}"
    )

    print("\n[系统日志] 正在自动提取 5W 关键信息并记录...")
    
    extract_messages = [{"role": "user", "content": prompt}]
    response = call_llm(extract_messages, stream=False, use_tools=False)
    
    if response and 'choices' in response and len(response['choices']) > 0:
        info = response['choices'][0]['message']['content'].strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"--- 记录时间: {timestamp} ---\n{info}\n\n"
        
        # 写入文件
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(record)
            print(f"[系统日志] 关键信息已追加到 {LOG_FILE}")
        except Exception as e:
            print(f"[系统日志] 记录失败: {str(e)}")

def parse_and_print_stream(response):
    """解析并实时打印流式响应内容"""
    full_content = ""
    for line in response:
        line_str = line.decode('utf-8').strip()
        if line_str.startswith("data: "):
            data_content = line_str[len("data: "):]
            if data_content == "[DONE]": break
            try:
                chunk = json.loads(data_content)
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        print(content, end="", flush=True)
                        full_content += content
            except:
                continue
    return full_content

def chat_with_search():
    if not API_KEY:
        print("错误: OPENAI_API_KEY 未设置。")
        return

    current_date = datetime.now().strftime("%Y-%m-%d")
    messages = [
        {
            "role": "system", 
            "content": f"你是一个具备文件系统操作、实时网页访问及历史记录搜索能力的 AI 助手。今天的日期是 {current_date}。你可以通过 search_chat_log 工具查找之前的聊天历史记录。当用户以 /search 开头或表达查找意图时，请务必使用该工具。"
        }
    ]

    print(f"--- 历史提取与搜索对话已开启 (模型: {MODEL}) ---")
    print("功能 1：每 5 次聊天自动提取 5W 关键信息到 D:\\chat-log\\log.txt")
    print("功能 2：支持 /search 命令或直接要求查找历史记录。\n")

    chat_count = 0

    try:
        while True:
            user_input = input("用户: ").strip()
            if not user_input: continue
            
            # 处理 /search 命令
            if user_input.startswith("/search "):
                search_query = user_input[len("/search "):].strip()
                # 强制触发工具调用逻辑（这里通过添加一个特定消息模拟）
                messages.append({"role": "user", "content": f"请帮我查找历史记录：{search_query}"})
            else:
                messages.append({"role": "user", "content": user_input})

            chat_count += 1

            # 处理对话逻辑 (包含工具调用)
            while True:
                response_data = call_llm(messages, stream=False)
                if not response_data or 'choices' not in response_data:
                    break
                
                message = response_data['choices'][0]['message']
                
                if message.get('tool_calls'):
                    tool_calls = message['tool_calls']
                    messages.append(message) 

                    for tool_call in tool_calls:
                        func_name = tool_call['function']['name']
                        func_args = json.loads(tool_call['function']['arguments'])
                        print(f"系统日志: 正在执行工具 [{func_name}]...")
                        
                        if func_name in AVAILABLE_TOOLS:
                            result = AVAILABLE_TOOLS[func_name](**func_args)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call['id'],
                                "name": func_name,
                                "content": result
                            })
                    continue
                else:
                    print("助手: ", end="", flush=True)
                    response_stream = call_llm(messages, stream=True)
                    if response_stream:
                        full_reply = parse_and_print_stream(response_stream)
                        messages.append({"role": "assistant", "content": full_reply})
                        print("\n")
                    break
            
            # 每 5 次聊天提取一次信息
            if chat_count % 5 == 0:
                extract_5w_info(messages)

    except KeyboardInterrupt:
        print("\n再见！")

if __name__ == "__main__":
    chat_with_search()
