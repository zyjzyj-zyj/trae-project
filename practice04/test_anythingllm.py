import json
import os
import requests # 导入 requests 模块
from dotenv import load_dotenv

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

ANYTHINGLLM_WORKSPACE_SLUG = os.getenv("ANYTHINGLLM_WORKSPACE_SLUG")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")

def anythingllm_query(message: str):
    if not ANYTHINGLLM_WORKSPACE_SLUG or not ANYTHINGLLM_API_KEY:
        return "错误: ANYTHINGLLM_WORKSPACE_SLUG 或 ANYTHINGLLM_API_KEY 未设置。"

    url = f"http://localhost:3001/api/v1/workspace/{ANYTHINGLLM_WORKSPACE_SLUG}/chat"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}"
    }
    payload = {"message": message}

    print(f"--- 调试信息 ---")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status() # 检查 HTTP 错误
        response_json = response.json()
        
        # 提取 AnythingLLM 的回复
        if 'textResponse' in response_json:
            return response_json['textResponse']
        elif 'text' in response_json:
            return response_json['text']
        elif 'error' in response_json:
            return f"AnythingLLM 错误: {response_json['error']}"
        else:
            return f"AnythingLLM 返回未知格式: {response.text}"

    except requests.exceptions.RequestException as e:
        return f"AnythingLLM 请求失败: {str(e)}"
    except json.JSONDecodeError:
        return f"AnythingLLM 返回非 JSON 响应: {response.text}"
    except Exception as e:
        return f"AnythingLLM 请求异常: {str(e)}"

if __name__ == "__main__":
    print("正在测试 AnythingLLM 查询功能...")
    result = anythingllm_query("你好，请问仓库里有什么文档？")
    print("\n--- 返回结果 ---")
    print(result)
