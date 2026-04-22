import json
import os
import urllib.request
import urllib.error
from dotenv import load_dotenv
from datetime import datetime

# 1. 加载配置
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# 2. 定义工具函数
def fetch_web_content(url):
    """访问网页并返回其内容"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"获取网页内容失败: {str(e)}"

AVAILABLE_TOOLS = {"fetch_web_content": fetch_web_content}

# 3. 定义工具 Schema
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "fetch_web_content",
            "description": "通过 URL 实时访问并抓取网页 HTML 内容。当用户提出需要联网、查看网址、获取新闻或实时信息时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "要访问的完整 URL"}
                },
                "required": ["url"]
            }
        }
    }
]

def call_llm(messages):
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS_SCHEMA,
        "tool_choice": "auto"
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def run_test():
    if not API_KEY:
        print("错误: OPENAI_API_KEY 未设置。")
        return

    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 构造包含日期感知的 System Prompt
    messages = [
        {
            "role": "system", 
            "content": f"你是一个具备网页访问能力的 AI 助手。今天的日期是 {current_date}。你可以通过访问 wttr.in 获取天气信息。"
        },
        {
            "role": "user", 
            "content": f"请帮我查一下今天（{current_date}）青城山的气温，访问 https://wttr.in/青城山?format=%t 获取数据，并告诉我今天的最高和最低气温（你可以访问 https://wttr.in/青城山 获取完整信息）。"
        }
    ]

    print(f"--- 正在执行天气功能测试 (模型: {MODEL}) ---")
    print(f"问题: 查一下今天（{current_date}）青城山的气温...\n")

    # 第一步：发送请求
    response_data = call_llm(messages)
    
    if 'choices' in response_data:
        message = response_data['choices'][0]['message']
        
        # 检查是否有工具调用
        if message.get('tool_calls'):
            tool_calls = message['tool_calls']
            messages.append(message)

            for tool_call in tool_calls:
                func_name = tool_call['function']['name']
                func_args = json.loads(tool_call['function']['arguments'])
                
                print(f"[系统日志] 正在调用工具: {func_name}({func_args})")
                
                if func_name in AVAILABLE_TOOLS:
                    result = AVAILABLE_TOOLS[func_name](**func_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "name": func_name,
                        "content": result
                    })
            
            # 第二步：获取最终回答
            print("[系统日志] 正在汇总信息...")
            final_response = call_llm(messages)
            if 'choices' in final_response:
                print("\nLLM 回复:")
                print(final_response['choices'][0]['message']['content'])
        else:
            print("LLM 没有调用工具。")
            print(message.get('content'))

if __name__ == "__main__":
    run_test()
