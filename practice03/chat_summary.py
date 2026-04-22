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
        # 在 system 之后或开头插入一个占位 user 消息
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

def summarize_history(messages):
    """将历史对话进行总结，确保不破坏工具链且消息序列合法"""
    if len(messages) <= 2:
        return messages

    # 1. 提取 system 消息
    system_msg = messages[0] if messages[0]['role'] == 'system' else None
    chat_history = messages[1:] if system_msg else messages

    # 2. 确定理想的分割点（70% 处）
    target_split = int(len(chat_history) * 0.7)
    
    # 3. 寻找最近的 user 消息作为实际分割点，确保不破坏工具调用链
    # 工具调用链 (Assistant -> Tool -> Assistant) 总是由 User 消息触发并结束
    actual_split = target_split
    for i in range(target_split, 0, -1):
        if chat_history[i]['role'] == 'user':
            actual_split = i
            break
    
    # 如果没找到 user 消息，就从 target_split 往后找
    if chat_history[actual_split]['role'] != 'user':
        for i in range(target_split, len(chat_history)):
            if chat_history[i]['role'] == 'user':
                actual_split = i
                break

    to_summarize = chat_history[:actual_split]
    to_keep = chat_history[actual_split:]

    if not to_summarize:
        return messages

    # 4. 构造总结请求
    summary_content = ""
    for msg in to_summarize:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        if content:
            summary_content += f"{role}: {content}\n"
    
    prompt = f"请将以下对话历史进行简要总结，保留核心信息，尤其是用户做过的操作和得到的关键结论：\n\n{summary_content}"
    
    print("\n[系统日志] 正在执行历史记录总结...")
    
    summary_messages = [{"role": "user", "content": prompt}]
    response = call_llm(summary_messages, stream=False, use_tools=False)
    
    if response and 'choices' in response and len(response['choices']) > 0:
        summary_text = response['choices'][0]['message']['content']
        print(f"[系统日志] 总结完成。摘要长度: {len(summary_text)} 字符。")
        
        # 5. 构造新的消息列表，确保符合 System -> User -> Assistant 交替规则
        new_messages = []
        if system_msg:
            new_messages.append(system_msg)
        
        # 将摘要作为 User 消息，告知模型之前的背景
        new_messages.append({
            "role": "user", 
            "content": f"（系统提示：以下是之前对话的摘要，请以此作为背景信息）\n\n{summary_text}"
        })
        
        # 添加模型对摘要的确认（作为 Assistant 消息）
        new_messages.append({
            "role": "assistant", 
            "content": "好的，我已经理解了之前的对话背景。请问接下来有什么我可以帮您的？"
        })
        
        # 拼接保留的原文
        # 如果 to_keep 的第一个消息是 Assistant，为了避免两个 Assistant 连在一起，
        # 我们插入一个简单的 User 确认或者直接跳过 Ack。
        # 但因为我们 split 在 User 消息处，to_keep[0] 一定是 User 消息。
        new_messages.extend(to_keep)
        return new_messages
    
    return messages

def check_and_summarize(messages):
    """检测是否需要总结"""
    # 过滤掉 tool 消息，只计算用户和助手的实际对话轮数
    chat_rounds = sum(1 for msg in messages if msg['role'] == 'user')
    # 计算总字符长度
    total_chars = sum(len(str(msg.get('content', ''))) for msg in messages)
    
    if chat_rounds > 5 or total_chars > 3000:
        return summarize_history(messages)
    return messages

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

def chat_with_summary():
    if not API_KEY:
        print("错误: OPENAI_API_KEY 未设置。")
        return

    current_date = datetime.now().strftime("%Y-%m-%d")
    messages = [
        {
            "role": "system", 
            "content": f"你是一个具备文件系统操作和实时网页访问能力的 AI 助手。今天的日期是 {current_date}。你可以通过调用工具来执行本地文件读写、目录管理或通过 URL 抓取网页内容。当用户要求你查看某个网址或搜索信息时，请务必使用 fetch_web_content 工具。"
        }
    ]

    print(f"--- 自动总结对话已开启 (模型: {MODEL}) ---")
    print("规则：轮数 > 5 或 长度 > 3000 字符时，自动压缩前 70% 的历史记录。\n")

    try:
        while True:
            user_input = input("用户: ").strip()
            if not user_input: continue
            
            # 1. 检查并执行总结逻辑 (在用户输入后，发送给 LLM 前)
            # 注意：这里我们选择在用户输入后立即检查，以确保发送给 LLM 的上下文是最新的且经过压缩的
            messages = check_and_summarize(messages)
            
            # 2. 添加用户当前输入
            messages.append({"role": "user", "content": user_input})

            # 3. 处理对话逻辑 (包含工具调用)
            while True:
                # 第一阶段：非流式请求，检查是否有工具调用
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
                    # 继续循环，让 LLM 处理工具结果
                    continue
                else:
                    # 没有工具调用，流式输出回复内容
                    # 既然 response_data 已经有了内容，我们其实可以直接打印，
                    # 但为了统一流式体验，我们这里再次发起流式请求（或者模拟流式输出）
                    print("助手: ", end="", flush=True)
                    # 重新发起一次流式请求
                    response_stream = call_llm(messages, stream=True)
                    if response_stream:
                        full_reply = parse_and_print_stream(response_stream)
                        messages.append({"role": "assistant", "content": full_reply})
                        print("\n")
                    break

    except KeyboardInterrupt:
        print("\n再见！")

if __name__ == "__main__":
    chat_with_summary()
