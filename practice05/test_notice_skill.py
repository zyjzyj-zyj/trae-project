import os
import json
from chat_summary import call_llm, list_available_skills, load_skill_content, AVAILABLE_TOOLS

def test_notice_skill(user_query, expected_prefix):
    print(f"\n--- 测试用户输入: '{user_query}' ---")
    
    # 初始化消息
    skills = list_available_skills()
    skills_json = json.dumps(skills, ensure_ascii=False, indent=2)
    
    messages = [
        {
            "role": "system", 
            "content": f"你是一个 AI 助手。你有以下可选技能：\n{skills_json}\n如果你认为需要使用其中的某个技能，请先调用 load_skill_content 工具获取该技能的详细执行指令，然后严格按照指令执行。"
        },
        {"role": "user", "content": user_query}
    ]

    # 第一步：调用 LLM，期望它调用 load_skill_content
    response = call_llm(messages, stream=False)
    if not response:
        print("错误: LLM 响应为空")
        return

    message = response['choices'][0]['message']
    if message.get('tool_calls'):
        tool_calls = message['tool_calls']
        messages.append(message)
        
        for tool_call in tool_calls:
            func_name = tool_call['function']['name']
            func_args = json.loads(tool_call['function']['arguments'])
            print(f"系统日志: LLM 决定执行工具 [{func_name}]，参数: {func_args}")
            
            if func_name in AVAILABLE_TOOLS:
                result = AVAILABLE_TOOLS[func_name](**func_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call['id'],
                    "name": func_name,
                    "content": result
                })
        
        # 第二步：再次调用 LLM，让它根据加载的技能内容生成回复
        response2 = call_llm(messages, stream=False)
        if response2:
            reply = response2['choices'][0]['message']['content']
            print(f"助手回复: {reply}")
            if reply.startswith(expected_prefix):
                print(f"验证成功: 回复以 '{expected_prefix}' 开头")
            else:
                print(f"验证失败: 回复未以 '{expected_prefix}' 开头")
    else:
        print("验证失败: LLM 没有调用 load_skill_content 工具")

if __name__ == "__main__":
    # 测试 case 1: 未说明部门
    test_notice_skill("帮我写一个关于明天下午开会的通知。", "XX部通知")
    
    # 测试 case 2: 说明是销售部
    test_notice_skill("帮我给销售部写一个关于下周团建的通知。", "销售部通知")
