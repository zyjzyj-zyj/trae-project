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
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功: 已创建文件 {file_path}"
    except Exception as e:
        return f"创建文件失败: {str(e)}"

def read_file(file_path):
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"读取文件失败: {str(e)}"

def fetch_web_content(url):
    """访问网页并返回其内容"""
    try:
        # 设置 User-Agent 模拟浏览器访问，避免部分网站拦截
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"获取网页内容失败: {str(e)}"

# --- 2. 映射工具函数 ---
AVAILABLE_TOOLS = {
    "list_files": list_files,
    "rename_file": rename_file,
    "delete_file": delete_file,
    "create_file": create_file,
    "read_file": read_file,
    "fetch_web_content": fetch_web_content
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
    }
]

# --- 4. 核心逻辑：带工具调用的聊天循环 ---

def call_llm(messages, stream=False):
    """封装 API 请求逻辑，支持流式和非流式"""
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS_SCHEMA,
        "tool_choice": "auto",
        "stream": stream
    }
    
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
            # 返回响应对象供流式解析
            return urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        print(f"API 错误: {e.code}")
        print(e.read().decode('utf-8'))
        return None
    except Exception as e:
        print(f"网络错误: {str(e)}")
        return None

def chat_with_tools():
    if not API_KEY:
        print("错误: OPENAI_API_KEY 未设置。")
        return

    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    messages = [
        {
            "role": "system", 
            "content": f"你是一个具备文件系统操作和实时网页访问能力的 AI 助手。今天的日期是 {current_date}。你可以通过调用工具来执行本地文件读写、目录管理或通过 URL 抓取网页内容。当用户要求你查看某个网址或搜索信息时，请务必使用 fetch_web_content 工具。"
        }
    ]

    print(f"--- 工具调用对话已开启 (模型: {MODEL}) ---")
    print("你可以说：'帮我看看当前目录有哪些文件' 或 '新建一个 test.txt 并写入内容'。\n")

    try:
        while True:
            user_input = input("用户: ").strip()
            if not user_input: continue
            messages.append({"role": "user", "content": user_input})

            # 第一阶段：非流式请求（因为我们需要检查 tool_calls，流式解析 tool_calls 比较复杂）
            response_data = call_llm(messages, stream=False)
            if not response_data: continue
            
            if 'choices' in response_data and len(response_data['choices']) > 0:
                message = response_data['choices'][0]['message']
                
                # 检查是否有工具调用请求
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
                    
                    # 第二阶段：将结果传回给 LLM，这次使用流式输出最终回复
                    print("助手: ", end="", flush=True)
                    response_stream = call_llm(messages, stream=True)
                    if response_stream:
                        full_reply = parse_and_print_stream(response_stream)
                        messages.append({"role": "assistant", "content": full_reply})
                        print("\n")
                else:
                    # 如果没有工具调用，直接以流式输出内容（为了统一体验）
                    # 重新发起一次流式请求以实现逐字显示
                    # (或者你可以直接打印 content，但为了符合用户“流式输出”要求，这里用流式重发)
                    print("助手: ", end="", flush=True)
                    response_stream = call_llm(messages, stream=True)
                    if response_stream:
                        full_reply = parse_and_print_stream(response_stream)
                        messages.append({"role": "assistant", "content": full_reply})
                        print("\n")

    except KeyboardInterrupt:
        print("\n再见！")

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

if __name__ == "__main__":
    chat_with_tools()
