import json
import os
import urllib.request
import urllib.error
from dotenv import load_dotenv
import sys
from datetime import datetime

# 加载项目根目录下的 .env 文件
# 由于脚本在 practice02 目录下，我们需要向上找一级
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"警告: 未找到 .env 文件 (路径: {dotenv_path})。")

# 从环境变量中读取配置
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def stream_chat():
    if not API_KEY:
        print("错误: OPENAI_API_KEY 未设置。请检查项目根目录下的 .env 文件。")
        return

    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")

    # 初始化历史记录，包含一个系统提示词
    messages = [
        {"role": "system", "content": f"你是一个有用的 AI 助手。今天的日期是 {current_date}。"}
    ]

    print(f"--- 已连接到 LLM (模型: {MODEL}) ---")
    print("输入你的问题开始对话（按 Ctrl+C 退出）\n")

    try:
        while True:
            # 1. 获取用户输入
            try:
                user_input = input("用户: ").strip()
            except EOFError:
                break
                
            if not user_input:
                continue
            
            # 2. 将用户消息添加到历史记录中，实现上下文关联
            messages.append({"role": "user", "content": user_input})

            # 3. 准备请求数据
            url = f"{BASE_URL.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": MODEL,
                "messages": messages,
                "stream": True  # 核心：开启流式输出模式
            }

            # 4. 发起请求
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=headers, 
                method='POST'
            )

            print("助手: ", end="", flush=True)
            assistant_reply = ""

            try:
                # 5. 处理流式响应
                with urllib.request.urlopen(req) as response:
                    for line in response:
                        line_str = line.decode('utf-8').strip()
                        if not line_str:
                            continue
                        
                        # OpenAI 协议的流式格式以 "data: " 开头
                        if line_str.startswith("data: "):
                            data_content = line_str[len("data: "):]
                            
                            # 结束标志
                            if data_content == "[DONE]":
                                break
                            
                            try:
                                chunk = json.loads(data_content)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    # 提取增量内容
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        # 实时打印到终端，不换行
                                        print(content, end="", flush=True)
                                        assistant_reply += content
                            except json.JSONDecodeError:
                                continue
                
                print("\n") # 对话结束换行
                
                # 6. 将助手的完整回复存入历史记录，以便下次对话携带上下文
                messages.append({"role": "assistant", "content": assistant_reply})

            except urllib.error.HTTPError as e:
                print(f"\nHTTP 错误: {e.code} {e.reason}")
                error_body = e.read().decode('utf-8')
                print(f"详情: {error_body}")
                break
            except urllib.error.URLError as e:
                print(f"\n请求失败: {e.reason}")
                break

    except KeyboardInterrupt:
        print("\n\n检测到退出指令，对话结束。再见！")

if __name__ == "__main__":
    stream_chat()
