# AI 智能体开发教学项目

这是一个基于 Python 的 AI 智能体开发教学项目，旨在帮助学习者掌握如何从零开始配置开发环境，并使用 Python 标准库与本地或云端 LLM (大语言模型) 进行交互。

## 详细实践内容 (按更新时间排序)

---

### [Practice 04 - AnythingLLM 知识库集成](file:///e:/Trae_projects/1/practice04/README.md)
*更新时间: 2026/4/22 16:06:15*

本项目在 Practice 03 的基础上，集成了 AnythingLLM 知识库查询功能，使 AI 助手能够访问本地文档仓库。

#### 新功能

1.  **AnythingLLM 查询工具 (`anythingllm_query`)**:
    *   通过 Python `requests` 库与本地 AnythingLLM API 交互。
    *   支持对指定工作区（Workspace）进行全文搜索和问答。
    *   处理中文编码，确保中文字符在请求和响应中正确显示。

2.  **智能工具切换**:
    *   更新了系统提示词。当用户提到“文档仓库”、“文件仓库”、“仓库”等关键词时，助手会自动优先调用 `anythingllm_query`。

3.  **对话总结与工具链集成**:
    *   保留了 Practice 03 中的自动对话总结功能，确保在长对话中依然能高效运行，同时不破坏工具调用逻辑。

#### 环境变量配置

在 `.env` 文件中添加以下配置：

```env
# AnythingLLM 配置
ANYTHINGLLM_API_KEY="你的_ANYTHINGLLM_API_KEY"
ANYTHINGLLM_WORKSPACE_SLUG="你的_WORKSPACE_SLUG"
```

*   **ANYTHINGLLM_API_KEY**: 在 AnythingLLM 设置 -> API Key 中生成。
*   **ANYTHINGLLM_WORKSPACE_SLUG**: 工作区的唯一标识符（通常在 URL 中可以看到，或通过 API 获取）。

#### 使用方法

1.  确保本地 AnythingLLM 服务已启动（默认端口 3001）。
2.  运行程序：
    ```bash
    python practice04/chat_summary.py
    ```
3.  在对话中输入，例如：“请问仓库里关于项目 A 的文档说了什么？”

#### 注意事项

*   程序依赖 Python `requests` 库。请运行 `pip install requests` 进行安装。
*   请确保 `.env` 中的 `ANYTHINGLLM_WORKSPACE_SLUG` 是正确的 UUID 或 Slug。

---

### [Practice 05 - 动态技能加载与管理](file:///e:/Trae_projects/1/practice05/README.md)
*更新时间: 2026/4/29 13:58:21*

本项目在 Practice 04 的基础上，增加了动态技能加载与管理功能。AI 助手可以根据需要，从 `.agents/skills` 目录中动态加载并执行特定的技能指令。

#### 新功能

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

#### 目录结构

```text
.agents/
└── skills/
    └── notice/
        └── SKILL.md  # 包含技能元数据和详细执行指令
```

#### 使用方法

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

#### 如何添加新技能

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

---

## 目录说明

### [practice01](file:///e:/trae_projects/1/practice01) - 基础连接与长文本分析
- [llm_test.py](file:///e:/trae_projects/1/practice01/llm_test.py): 演示如何读取配置文件、使用 `urllib` 标准库发起 POST 请求。
- **功能**: 支持从 `long_text.txt` 中读取长文本并向 LLM 提问，同时统计 Token 消耗、生成时间及生成速度。
- **教学目标**: 理解 OpenAI 兼容协议的基础请求格式。

### [practice02](file:///e:/trae_projects/1/practice02) - 对话历史、流式输出与工具调用
- [chat_stream.py](file:///e:/trae_projects/1/practice02/chat_stream.py): 基础流式对话练习。
- [chat_tools.py](file:///e:/trae_projects/1/practice02/chat_tools.py): 进阶工具调用练习。
- **核心功能**:
  1. **对话循环**: 支持持续对话及上下文记忆。
  2. **流式输出**: 实时展示 AI 回复。
  3. **日期自动附加**: 在 System Prompt 中自动附加当前日期，使 AI 具备时间感知能力。
  4. **工具调用 (Function Calling)**: LLM 可以根据用户指令调用本地 Python 函数执行以下操作：
     - 列出目录文件（含大小、修改时间等）。
     - 重命名文件或目录。
     - 删除文件。
     - 创建新文件并写入内容。
     - 读取文件内容。
     - **网页访问**: 通过 URL 访问网页并获取 HTML 内容（用于分析网页信息）。
- **教学目标**: 掌握如何定义 Tools Schema、处理 `tool_calls` 以及将执行结果反馈给 LLM。

### [practice03](file:///e:/trae_projects/1/practice03) - 对话自动总结与上下文管理
- [chat_summary.py](file:///e:/trae_projects/1/practice03/chat_summary.py): 演示如何通过总结历史对话来管理长上下文。
- [chat_search.py](file:///e:/trae_projects/1/practice03/chat_search.py): 进阶长对话管理，包含关键信息提取与历史记录搜索。
- **核心功能**:
  1. **自动总结触发**: 当对话轮数超过 5 轮或总字符数超过 3000 时，自动触发总结逻辑。
  2. **70/30 压缩策略**: 将历史记录的前 70% 内容进行压缩概括，保留最后 30% 的原文，拼接后作为新的上下文。
  3. **5W 关键信息提取**: 每 5 轮对话自动提取一次 5W (Who, What, When, Where, Why) 信息并记录到 `D:\chat-log\log.txt`。
  4. **历史记录搜索**: 支持通过 `/search` 命令或自然语言触发 `search_chat_log` 工具，读取日志文件并结合用户请求给出查找结果。
  5. **集成工具调用**: 继承了 practice02 中的所有文件操作和网页访问工具。
- **教学目标**: 理解长对话背景下的上下文窗口限制，学习如何通过 LLM 总结和持久化存储来实现"长短期记忆"管理。

### [practice04](file:///e:/trae_projects/1/practice04) - AnythingLLM 知识库集成
- [chat_summary.py](file:///e:/trae_projects/1/practice04/chat_summary.py): 在 Practice 03 基础上集成了 AnythingLLM 知识库查询功能。
- [test_anythingllm.py](file:///e:/trae_projects/1/practice04/test_anythingllm.py): AnythingLLM 查询功能独立测试脚本。
- **核心功能**:
  1. **AnythingLLM 查询工具 (`anythingllm_query`)**:
     - 使用 Python `requests` 库与本地 AnythingLLM API 交互。
     - 支持对指定工作区（Workspace）进行全文搜索和问答。
     - 处理中文编码，确保中文字符在请求和响应中正确显示。
  2. **智能工具切换**:
     - 更新了系统提示词。当用户提到"文档仓库"、"文件仓库"、"仓库"等关键词时，助手会自动优先调用 `anythingllm_query`。
  3. **对话总结与工具链集成**:
     - 保留了 Practice 03 中的自动对话总结功能，确保在长对话中依然能高效运行，同时不破坏工具调用逻辑。
- **环境变量配置**: 在 `.env` 文件中添加以下配置：
  ```ini
  ANYTHINGLLM_API_KEY=你的_ANYTHINGLLM_API_KEY
  ANYTHINGLLM_WORKSPACE_SLUG=你的_WORKSPACE_SLUG
  ```
- **教学目标**: 学习如何将本地知识库集成到 AI 助手中，实现基于私有文档的问答能力。

### [practice05](file:///e:/trae_projects/1/practice05) - 动态技能加载与管理
- [chat_summary.py](file:///e:/trae_projects/1/practice05/chat_summary.py): 在 Practice 04 基础上增加了动态技能发现与加载功能。
- [test_notice_skill.py](file:///e:/trae_projects/1/practice05/test_notice_skill.py): 技能功能的自动化测试脚本。
- **核心功能**:
  1. **动态技能发现 (`list_available_skills`)**:
     - 在启动时自动扫描 `.agents/skills/*/SKILL.md` 文件。
     - 从 YAML front matter 中提取技能的 `name` 和 `description`。
     - 将可用技能列表通过 system prompt 告知 LLM。
  2. **动态技能加载 (`load_skill_content`)**:
     - 这是一个新的工具函数，供 LLM 在判断需要使用某个技能时调用。
     - 读取技能文件的正文内容（YAML front matter 之后的部分），并返回给 LLM。
  3. **技能执行**:
     - LLM 加载技能指令后，会严格按照指令中的规则执行任务。
     - 示例技能：`notice`（通知编写技能），根据用户是否指定部门自动调整开头。
- **教学目标**: 掌握如何实现 AI 助手的插件化/技能化扩展，学习如何让 LLM 根据上下文动态加载并遵循特定的执行指令。

## 开发环境配置

1. **Python 环境**: 建议使用 Python 3.12+。
2. **初始化**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **配置 .env**:
   将 `.env` 文件放置在项目根目录，包含以下配置：
   ```ini
   OPENAI_API_KEY=your_api_key
   OPENAI_BASE_URL=http://127.0.0.1:1234/v1
   OPENAI_MODEL=qwen3.5 4B
   ```

## 运行示例

```powershell
# 运行 practice01
.\venv\Scripts\python.exe practice01/llm_test.py

# 运行 practice02
.\venv\Scripts\python.exe practice02/chat_stream.py

# 运行 practice03
.\venv\Scripts\python.exe practice03/chat_summary.py
.\venv\Scripts\python.exe practice03/chat_search.py

# 运行 practice04
.\venv\Scripts\python.exe practice04/chat_summary.py
.\venv\Scripts\python.exe practice04/test_anythingllm.py

# 运行 practice05
.\venv\Scripts\python.exe practice05/chat_summary.py
.\venv\Scripts\python.exe practice05/test_notice_skill.py
```
