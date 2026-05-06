import json
import os
import urllib.request
import urllib.error
from dotenv import load_dotenv
import sys
import time
from datetime import datetime
import re
import argparse

# 加载项目根目录下的 .env 文件
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# 从环境变量中读取配置
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# 获取当前脚本所在的目录路径 (practice06 目录)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 1. 定义工具功能 (Tools) ---

def list_files(directory="."):
    """列出目录下所有文件及其基本属性。路径相对于 practice06 目录。"""
    try:
        # 强制基于 BASE_DIR 拼接路径
        target_dir = os.path.abspath(os.path.join(BASE_DIR, directory))

        if not os.path.isdir(target_dir):
            return f"错误: {target_dir} 不是一个有效的目录。"
        files_info = []
        for entry in os.scandir(target_dir):
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

def read_file(file_path):
    """读取文件内容。路径相对于 practice06 目录。"""
    try:
        # 强制基于 BASE_DIR 拼接路径
        full_path = os.path.abspath(os.path.join(BASE_DIR, file_path))

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"读取文件失败: {str(e)}"

def create_file(file_path, content=""):
    """新建文件并写入内容。路径相对于 practice06 目录，如果目录不存在则自动创建。"""
    try:
        # 强制基于 BASE_DIR 拼接路径
        full_path = os.path.abspath(os.path.join(BASE_DIR, file_path))

        directory = os.path.dirname(full_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功: 已创建文件 {full_path}"
    except Exception as e:
        return f"创建文件失败: {str(e)}"

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

AVAILABLE_TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "create_file": create_file,
    "fetch_web_content": fetch_web_content
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出指定目录下的文件和文件夹。",
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
            "name": "read_file",
            "description": "读取指定文件的内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "创建一个新文件并写入内容。如果目录不存在会自动创建。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件保存路径"},
                    "content": {"type": "string", "description": "文件内容"}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_web_content",
            "description": "获取指定 URL 的网页 HTML 内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "网页 URL"}
                },
                "required": ["url"]
            }
        }
    }
]

# --- 2. 核心类与函数 ---

class ChainedCallContext:
    def __init__(self, max_iterations=10):
        self.steps = []
        self.variables = {}
        self.max_iterations = max_iterations
        self.current_iteration = 0

    def add_step(self, tool_name, arguments, result):
        self.steps.append({
            "step": len(self.steps) + 1,
            "tool": tool_name,
            "arguments": arguments,
            "result": result
        })

    def set_variable(self, name, value):
        self.variables[name] = value

    def get_variable(self, name):
        return self.variables.get(name)

def call_llm(messages, use_tools=True):
    """封装 API 请求逻辑"""
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.1  # 降低随机性，使输出更稳定
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
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"LLM 调用失败: {str(e)}")
        return None

def build_analysis_prompt(user_request, context):
    """构建分析提示词"""
    history_str = ""
    if context.steps:
        history_str = "\n已执行的步骤历史：\n"
        for step in context.steps:
            # 截断极长的结果，避免 Prompt 超过模型限制，但保留足够的上下文
            result_str = str(step['result'])
            if len(result_str) > 5000:
                result_str = result_str[:5000] + "...(内容已截断)"
            history_str += f"- 步骤 {step['step']}: 调用工具 [{step['tool']}]，参数: {json.dumps(step['arguments'], ensure_ascii=False)}，结果: {result_str}\n"
    
    prompt = f"""用户原始请求：{user_request}
{history_str}
决策规则说明：
1. 分析用户原始请求，列出完成任务所需的步骤。
2. 对于涉及读取文件内容并计算的任务，第一步必须是调用 read_file 工具获取真实数据。
3. 严禁编造、猜测或假设文件内容。只有工具执行结果返回的内容才是真实可靠的数据。
4. 检查“已执行的步骤历史”，确认是否已经获得了所有必要的真实文件内容。
5. 如果所有必要信息已获得并满足用户请求，请返回 {{"done": true, "answer": "..."}}。
6. 如果还需要更多信息或尚未读取文件内容，请决定下一步调用哪个工具（如 read_file）。
7. 请避免重复执行相同的工具调用（除非结果报错或不完整）。

JSON 输出格式要求：
- 如果任务完成：{{"done": true, "answer": "最终回答内容"}}
- 如果需要继续调用工具：{{"done": false, "tool_call": {{"name": "工具名称", "arguments": {{"参数名": "参数值"}}}}}}
"""
    return prompt

def extract_json(text):
    """从文本中提取 JSON 内容"""
    if not text:
        return None
    # 尝试匹配 markdown 代码块
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        # 尝试寻找第一个 { 和最后一个 }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end+1]
    
    try:
        return json.loads(text)
    except:
        return None

def execute_chained_tool_call(user_request, max_iterations=10):
    """执行链式工具调用的完整流程"""
    context = ChainedCallContext(max_iterations=max_iterations)
    
    system_prompt = """你是一个具备链式工具调用能力的 AI 助手。
规则：
1. 你可以根据上一步工具调用的结果来决定下一步的操作。
2. 存在顺序依赖关系时，请一步步执行。例如：先列出文件，再读取感兴趣的文件。
3. 所有文件路径都相对于 practice06 目录，你只需要传入文件名或相对路径即可，不要传入绝对路径。
4. 当用户要求读取指定文件内容（如数字计算）时，必须调用 read_file 工具获取真实内容。
5. 严禁编造或推测文件内容。如果 read_file 返回的内容不是纯数字（在需要数字计算时），请向用户报告错误。
6. 只有在获取到所有必要的工具执行结果后，才能给出最终回答。
7. 你可以使用上下文变量来存储中间状态。
8. 每次决策必须以规定的 JSON 格式返回。

链式调用示例：
用户请求：读取 1.txt 和 2.txt 并求和。
步骤 1：调用 read_file(file_path="1.txt")，得到结果 "10"。
步骤 2：调用 read_file(file_path="2.txt")，得到结果 "20"。
步骤 3：计算 10+20=30，返回 {"done": true, "answer": "结果是 30"}。
"""
    
    # 基础消息历史只包含 system prompt
    messages = [{"role": "system", "content": system_prompt}]
    
    print(f"\n>>> 开始处理请求: {user_request}")
    
    for i in range(max_iterations):
        context.current_iteration = i + 1
        print(f"\n--- 迭代 {context.current_iteration}/{max_iterations} ---")
        
        analysis_prompt = build_analysis_prompt(user_request, context)
        # 构造当前轮次的完整消息列表
        current_messages = messages + [{"role": "user", "content": analysis_prompt}]
        
        response_data = call_llm(current_messages)
        if not response_data:
            return "错误：无法获取 LLM 响应。"
        
        message = response_data['choices'][0]['message']
        content = message.get('content') or ""
        tool_calls = message.get('tool_calls')
        
        print(f"LLM 响应内容: {content[:500]}..." if len(content) > 500 else f"LLM 响应内容: {content}")
        
        decision = None
        # 优先尝试从 content 中提取 JSON
        if content:
            decision = extract_json(content)
        
        # 如果 content 解析失败或没有 content，但有 tool_calls
        if not decision and tool_calls:
            print("正在使用 tool_calls 进行决策...")
            tc = tool_calls[0]
            decision = {
                "done": False,
                "tool_call": {
                    "name": tc['function']['name'],
                    "arguments": json.loads(tc['function']['arguments'])
                }
            }
        
        if not decision:
            # 兜底：如果 LLM 没有按 JSON 返回，且没有 tool_calls，报错
            return f"错误：解析决策失败。LLM 输出内容：{content}"
        
        # --- 增加验证逻辑 ---
        if decision.get("done"):
            # 如果请求中包含读取文件的需求，但历史中没有 read_file 步骤
            needs_read = any(kw in user_request for kw in ["读取", "read", ".txt"])
            has_read = any(step['tool'] == "read_file" for step in context.steps)
            
            if needs_read and not has_read:
                print("系统检测：缺少必要的 read_file 步骤。强制要求 LLM 读取文件。")
                decision["done"] = False
                # 构造一条系统提示，要求 LLM 补充读取步骤
                messages.append({"role": "system", "content": "拒绝该结果。你尚未通过 read_file 工具获取文件的真实内容。请先调用 read_file 工具读取文件内容，严禁编造数据。"})
                continue
            
            print(f"任务完成！最终回答: {decision.get('answer')}")
            return decision.get("answer")
        
        tool_info = decision.get("tool_call")
        if not tool_info:
            return "错误：LLM 返回了未完成状态但没有提供工具调用信息。"
        
        func_name = tool_info.get("name")
        func_args = tool_info.get("arguments", {})
        
        print(f"执行工具: {func_name}, 参数: {json.dumps(func_args, ensure_ascii=False)}")
        
        if func_name in AVAILABLE_TOOLS:
            try:
                result = AVAILABLE_TOOLS[func_name](**func_args)
                context.add_step(func_name, func_args, result)
            except Exception as e:
                error_msg = f"工具执行异常: {str(e)}"
                context.add_step(func_name, func_args, error_msg)
        else:
            error_msg = f"错误：未知工具 {func_name}"
            context.add_step(func_name, func_args, error_msg)

    return "错误：达到最大迭代次数，任务未完成。"

# --- 3. 测试用例 ---

def run_tests(test_id=None):
    """运行测试用例"""
    tests = [
        {
            "id": 1,
            "name": "文件搜索链式调用",
            "request": "查找 practice06 目录下所有包含 def 关键词的文件并总结这些文件的主要内容。"
        },
        {
            "id": 2,
            "name": "多文件操作",
            "setup": lambda: (create_file("1.txt", "1314"), create_file("2.txt", "114514")),
            "request": "读取 1.txt 和 2.txt 两个文件，文件内容都是正整数，把两个数相加的和写入 result.txt 文件。"
        },
        {
            "id": 3,
            "name": "网页处理链式调用",
            "request": "访问 https://www.nsu.edu.cn/HTML/news/2024/06/article_3974.html 并总结页面内容，保存到 practice07/summary.txt。"
        }
    ]

    for test in tests:
        if test_id is None or test_id == test["id"]:
            print(f"\n\n=== 测试 {test['id']}: {test['name']} ===")
            if "setup" in test:
                test["setup"]()
            execute_chained_tool_call(test["request"])

def main():
    parser = argparse.ArgumentParser(description="链式工具调用客户端")
    parser.add_argument("--test", type=int, choices=[1, 2, 3], help="运行指定的测试用例 (1, 2, 或 3)")
    parser.add_argument("--test-all", action="store_true", help="运行所有测试用例")
    
    args = parser.parse_args()

    if args.test_all:
        run_tests()
    elif args.test:
        run_tests(args.test)
    else:
        # 进入交互模式
        print("\n" + "="*50)
        print("欢迎使用链式工具调用助手！")
        print("您可以输入您的请求，助手将自动拆解步骤并调用工具完成任务。")
        print("输入 'exit', 'quit' 或 '退出' 结束程序。")
        print("="*50)

        while True:
            try:
                user_input = input("\n用户请求 > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['exit', 'quit', '退出']:
                    print("再见！")
                    break
                
                execute_chained_tool_call(user_input)
            except KeyboardInterrupt:
                print("\n程序已终止。")
                break
            except Exception as e:
                print(f"\n发生错误: {str(e)}")

if __name__ == "__main__":
    main()
