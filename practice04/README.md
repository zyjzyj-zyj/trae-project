# Practice 04 - AnythingLLM 知识库集成

本项目在 Practice 03 的基础上，集成了 AnythingLLM 知识库查询功能，使 AI 助手能够访问本地文档仓库。

## 新功能

1.  **AnythingLLM 查询工具 (`anythingllm_query`)**:
    *   通过 Python `requests` 库与本地 AnythingLLM API 交互。
    *   支持对指定工作区（Workspace）进行全文搜索和问答。
    *   处理中文编码，确保中文字符在请求和响应中正确显示。

2.  **智能工具切换**:
    *   更新了系统提示词。当用户提到“文档仓库”、“文件仓库”、“仓库”等关键词时，助手会自动优先调用 `anythingllm_query`。

3.  **对话总结与工具链集成**:
    *   保留了 Practice 03 中的自动对话总结功能，确保在长对话中依然能高效运行，同时不破坏工具调用逻辑。

## 环境变量配置

在 `.env` 文件中添加以下配置：

```env
# AnythingLLM 配置
ANYTHINGLLM_API_KEY="你的_ANYTHINGLLM_API_KEY"
ANYTHINGLLM_WORKSPACE_SLUG="你的_WORKSPACE_SLUG"
```

*   **ANYTHINGLLM_API_KEY**: 在 AnythingLLM 设置 -> API Key 中生成。
*   **ANYTHINGLLM_WORKSPACE_SLUG**: 工作区的唯一标识符（通常在 URL 中可以看到，或通过 API 获取）。

## 使用方法

1.  确保本地 AnythingLLM 服务已启动（默认端口 3001）。
2.  运行程序：
    ```bash
    python practice04/chat_summary.py
    ```
3.  在对话中输入，例如：“请问仓库里关于项目 A 的文档说了什么？”

## 注意事项

*   程序依赖 Python `requests` 库。请运行 `pip install requests` 进行安装。
*   请确保 `.env` 中的 `ANYTHINGLLM_WORKSPACE_SLUG` 是正确的 UUID 或 Slug。
