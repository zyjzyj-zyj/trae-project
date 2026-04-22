import json
import os
import sys
from unittest.mock import patch, MagicMock

# 将当前目录加入 python 路径以便导入 chat_summary
sys.path.append(os.path.dirname(__file__))

import chat_summary

# 模拟 API 响应
def mock_call_llm(messages, stream=False, use_tools=True):
    if not stream:
        # 如果是总结请求 (messages 只有一个 user 消息且包含 '请将以下对话历史进行简要总结')
        if len(messages) == 1 and "请将以下对话历史进行简要总结" in str(messages[0].get('content', '')):
            return {
                "choices": [{
                    "message": {
                        "content": "这是一个对话摘要。用户之前做了一些操作。"
                    }
                }]
            }
        # 普通聊天请求 (非工具调用)
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "这是一条正常的回复。",
                    "tool_calls": None
                }
            }]
        }
    else:
        # 流式响应
        class MockResponse:
            def __iter__(self):
                chunks = [
                    'data: {"choices": [{"delta": {"content": "这是一条"}}]}',
                    'data: {"choices": [{"delta": {"content": "流式回复。"}}]}',
                    'data: [DONE]'
                ]
                for chunk in chunks:
                    yield chunk.encode('utf-8')
        return MockResponse()

def test_summary_logic():
    print("--- 开始测试自动总结逻辑 ---")
    
    # 初始化消息
    messages = [
        {"role": "system", "content": "你是一个助手。"}
    ]
    
    # 修改 check_and_summarize 中的阈值以便快速测试
    with patch('chat_summary.call_llm', side_effect=mock_call_llm):
        # 模拟 3 轮对话
        for i in range(3):
            print(f"\n[测试] 第 {i+1} 轮对话")
            user_input = f"你好，这是第 {i+1} 次对话内容。"
            
            # 手动模拟 chat_with_summary 循环中的逻辑
            # 1. 检查总结
            # 我们强制让它在第3轮开始前执行总结
            if i == 2:
                print("[测试模拟] 强制执行总结逻辑...")
                messages = chat_summary.summarize_history(messages)
                print(f"[测试] 总结后的消息数: {len(messages)}")
                # 检查消息序列
                for idx, msg in enumerate(messages):
                    print(f"  {idx}: {msg['role']}")
                
                if any("（系统提示：以下是之前对话的摘要" in str(msg.get('content', '')) for msg in messages):
                    print("[测试成功] 已包含摘要内容。")
                else:
                    print("[测试失败] 未包含摘要内容。")
                    return False

            # 2. 添加用户输入
            messages.append({"role": "user", "content": user_input})
            
            # 3. 模拟 LLM 回复
            print("助手: ", end="")
            response_stream = chat_summary.call_llm(messages, stream=True)
            full_reply = chat_summary.parse_and_print_stream(response_stream)
            messages.append({"role": "assistant", "content": full_reply})
            print()
            
    print("\n--- 测试完成 ---")
    return True

if __name__ == "__main__":
    test_summary_logic()
