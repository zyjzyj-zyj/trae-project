# Practice 05 - 动态技能加载与管理

本项目在 Practice 04 的基础上，增加了动态技能加载与管理功能。AI 助手可以根据需要，从 `.agents/skills` 目录中动态加载并执行特定的技能指令。

## 新功能

1.  **动态技能发现 (`list_available_skills`)**:
    *   在启动时自动扫描 `.agents/skills/*/SKILL.md` 文件。
    *   从 YAML front matter 中提取技能的 `name` 和 `description`。
    *   将可用技能列表通过 system prompt 告知 LLM。

2.  **动态技能加载 (`load_skill_content`)**:
    *   这是一个新的工具函数，供 LLM 在判断需要使用某个技能时调用。
    *   读取技能文件的正文内容（YAML front matter 之后的部分），并返回给 LLM。

3.  **技能执行**:
    *   LLM 加载技能指令后，会严格按照指令中的规则执行任务。
    *   示例技能：`notice`（通知编写技能），根据用户是否指定部门自动调整开头。

## 目录结构

```text
.agents/
└── skills/
    └── notice/
        └── SKILL.md  # 包含技能元数据和详细执行指令
```

## 使用方法

1.  确保已安装依赖：
    ```bash
    pip install PyYAML requests python-dotenv
    ```
2.  运行程序：
    ```bash
    python practice05/chat_summary.py
    ```
3.  在对话中尝试使用技能，例如：
    *   “帮我写一个关于明天下午开会的通知。”（未指定部门，应以“XX部通知”开头）
    *   “帮我给销售部写一个关于下周团建的通知。”（指定了销售部，应以“销售部通知”开头）

## 如何添加新技能

1.  在 `.agents/skills` 下创建一个新文件夹（如 `my_skill`）。
2.  在该文件夹下创建 `SKILL.md`。
3.  添加 YAML front matter（包含 `name` 和 `description`）。
4.  在 front matter 之后添加详细的技能执行指令。

示例 `SKILL.md`:
```markdown
---
name: translate
description: 将文本翻译成指定语言
---
# 翻译技能指令
1. 识别目标语言。
2. 保持专业、准确的语气。
```
