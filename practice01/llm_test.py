import json
import time
import os
import urllib.request
import urllib.error
from dotenv import load_dotenv

# 加载项目根目录下的 .env 文件
# 由于脚本在 practice01 目录下，我们需要向上找一级
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"警告: 未找到 .env 文件 (路径: {dotenv_path})。请确保已从 env.example 复制并填写参数。")

# 从环境变量中读取配置
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

print(f"DEBUG: 加载配置 - BASE_URL: {BASE_URL}, MODEL: {MODEL}")

def ask_llm(question, context_text):
    if not API_KEY:
        print("错误: OPENAI_API_KEY 未设置。")
        return

    # 准备请求数据
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构造针对长文本的 Prompt
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个严谨的文章分析助手。请只根据用户提供的文本内容回答问题。"},
            {"role": "user", "content": f"以下是参考文章内容：\n\n{context_text}\n\n问题：{question}\n请根据上述内容给出准确答案。"}
        ],
        "temperature": 0.0  # 提取类任务使用 0 度更稳定
    }

    # print(f"正在请求 LLM (模型: {MODEL}, 接口: {url})...")
    
    try:
        # 使用 Python 标准库 urllib 发起 POST 请求
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            res_content = response.read().decode('utf-8')
            res_data = json.loads(res_content)
            
            # 解析响应内容
            if 'choices' in res_data and len(res_data['choices']) > 0:
                choice = res_data['choices'][0]
                answer = choice.get('message', {}).get('content', '')
                print(f"\nAI 回答: {answer}\n")
            else:
                print("\n错误: 响应数据中缺少 'choices' 字段或为空。")
                print(f"原始响应内容: {res_content}")
            
    except urllib.error.HTTPError as e:
        print(f"HTTP 错误: {e.code} {e.reason}")
        res_body = e.read().decode('utf-8')
        print(f"响应内容: {res_body}")
    except urllib.error.URLError as e:
        print(f"请求失败: {e.reason}")
    except Exception as e:
        print(f"发生未知错误: {type(e).__name__}: {e}")

if __name__ == "__main__":
    # 尝试从 practice01/long_text.txt 读取长文本
    long_text_path = os.path.join(os.path.dirname(__file__), 'long_text.txt')
    if os.path.exists(long_text_path):
        with open(long_text_path, 'r', encoding='utf-8') as f:
            content_text = f.read()
            print(f"成功加载文本内容 (文件: {long_text_path})")
    else:
        print(f"警告: 未找到 {long_text_path}。请将你的文本粘贴到该文件中。")
        content_text = "（未提供参考文本内容）"

    print("程序启动，按 Ctrl+C 可以退出程序。")
    try:
        while True:
            user_input = input("请输入你的问题：")
            if not user_input.strip():
                continue
            ask_llm(user_input, content_text)
    except KeyboardInterrupt:
        print("\n程序已退出。")
