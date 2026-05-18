# 网页内容摘要工具 - 测试文档

## 一、测试概述

### 1.1 测试目标
验证网页内容摘要工具的各项功能是否符合需求：
- 配置文件读取功能
- 命令行参数解析功能
- 网页抓取功能
- 正文内容提取功能
- 本地模型加载功能
- 摘要生成功能
- 结果输出功能

### 1.2 测试范围
| 模块 | 测试类型 |
| --- | --- |
| `load_config()` | 单元测试 |
| `parse_args()` | 单元测试 |
| `fetch_webpage()` | 集成测试 |
| `extract_content()` | 单元测试 |
| `load_model()` | 集成测试 |
| `generate_summary()` | 集成测试 |
| `print_results()` | 单元测试 |
| `main()` | 端到端测试 |

### 1.3 测试环境
- Python 3.8+
- 测试用配置文件：`test_config.yaml`
- 测试用 HTML 文件：`test_page.html`
- Mock 模型（用于测试）

---

## 二、单元测试用例

### 2.1 `load_config()` 测试用例

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-001 | 配置文件不存在 | 不存在的文件路径 | 返回默认配置 |
| TC-002 | 正常读取配置文件 | 完整的 config.yaml | 返回包含所有参数的字典 |
| TC-003 | 配置文件格式错误 | 无效的 YAML 文件 | 抛出 ValueError |
| TC-004 | 配置文件部分缺失 | 缺少部分参数的 config.yaml | 合并默认配置 |

**测试数据示例**：
```yaml
# 完整配置示例
model_type: qwen
model_path: ./models/
max_tokens: 300
timeout: 30
```

---

### 2.2 `parse_args()` 测试用例

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-005 | 必填参数 --url | `--url https://example.com` | args.url 包含 URL |
| TC-006 | 缺少 --url 参数 | 无 --url | 抛出参数错误 |
| TC-007 | 指定 --config 参数 | `--url xxx --config custom.yaml` | args.config = 'custom.yaml' |
| TC-008 | 指定 --model-type 参数 | `--url xxx --model-type llama` | args.model_type = 'llama' |

---

### 2.3 `extract_content()` 测试用例

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-009 | 正常 HTML 提取 | 包含正文的 HTML | 返回正文文本 |
| TC-010 | 去除 script 标签 | 包含 script 的 HTML | 不包含 script 内容 |
| TC-011 | 去除 nav 标签 | 包含导航的 HTML | 不包含导航内容 |
| TC-012 | 去除 footer 标签 | 包含页脚的 HTML | 不包含页脚内容 |
| TC-013 | 空 HTML | 空字符串 | 返回空字符串 |

**测试数据示例**：
```html
<!DOCTYPE html>
<html>
<head><title>测试页面</title></head>
<body>
    <nav>导航栏内容</nav>
    <script>alert('test')</script>
    <h1>文章标题</h1>
    <p>这是正文第一段。</p>
    <p>这是正文第二段。</p>
    <footer>页脚内容</footer>
</body>
</html>
```

---

### 2.4 `print_results()` 测试用例

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-014 | 正常输出 | 完整的参数 | 按格式输出所有信息 |
| TC-015 | 空标题 | title="" | 输出标题行为空 |
| TC-016 | 长摘要 | 超过 300 字的摘要 | 正确显示完整摘要 |

---

## 三、集成测试用例

### 3.1 `fetch_webpage()` 集成测试

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-017 | 正常 HTTP 请求 | 有效的 HTTP URL | 返回 HTML 内容和标题 |
| TC-018 | 正常 HTTPS 请求 | 有效的 HTTPS URL | 返回 HTML 内容和标题 |
| TC-019 | 404 错误 | 不存在的 URL | 抛出 HTTPError |
| TC-020 | 网络超时 | 超时设置内无响应 | 抛出超时异常 |
| TC-021 | 无效 URL | 格式错误的 URL | 抛出 ValueError |

---

### 3.2 `load_model()` 集成测试

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-022 | 加载 Qwen 模型 | model_type='qwen', 有效路径 | 返回模型对象 |
| TC-023 | 加载 Llama 模型 | model_type='llama', 有效路径 | 返回模型对象 |
| TC-024 | 加载 ChatGLM 模型 | model_type='chatglm', 有效路径 | 返回模型对象 |
| TC-025 | 不支持的模型类型 | model_type='invalid' | 抛出 ValueError |
| TC-026 | 模型路径不存在 | 无效的 model_path | 抛出 FileNotFoundError |

---

### 3.3 `generate_summary()` 集成测试

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-027 | 正常生成摘要 | 模型 + 正文内容 | 返回 100-300 字摘要 |
| TC-028 | 短正文内容 | 少于 100 字的内容 | 仍能生成摘要 |
| TC-029 | 长正文内容 | 超过 10000 字的内容 | 成功生成摘要 |
| TC-030 | 空内容 | content="" | 返回空或错误提示 |

---

## 四、端到端测试

| 用例 ID | 测试场景 | 输入 | 预期结果 |
| --- | --- | --- | --- |
| TC-031 | 完整流程测试 | `--url https://example.com` | 输出完整摘要信息 |
| TC-032 | 中文网页测试 | 中文网页 URL | 正确处理中文编码 |
| TC-033 | 英文网页测试 | 英文网页 URL | 正确生成英文摘要 |
| TC-034 | 自定义配置测试 | `--url xxx --config custom.yaml` | 使用自定义配置 |
| TC-035 | 指定模型测试 | `--url xxx --model-type llama` | 使用指定模型 |

---

## 五、测试步骤

### 5.1 单元测试步骤

```plaintext
1. 创建测试配置文件 test_config.yaml
2. 创建测试 HTML 文件 test_page.html
3. 编写单元测试脚本 test_web_summarizer.py
4. 运行测试：python -m pytest test_web_summarizer.py -v
```

### 5.2 集成测试步骤

```plaintext
1. 准备测试用本地模型（或使用 Mock 模型）
2. 准备测试网页服务器
3. 编写集成测试脚本 test_integration.py
4. 运行集成测试：python -m pytest test_integration.py -v
```

### 5.3 手动验证步骤

```plaintext
1. 复制 config.example.yaml 为 config.yaml
2. 编辑 config.yaml，设置模型路径
3. 运行：python web_summarizer.py --url https://example.com
4. 检查输出是否符合预期格式
```

---

## 六、测试工具

| 工具 | 用途 |
| --- | --- |
| pytest | 单元测试框架 |
| unittest.mock | Mock 对象和函数 |
| requests-mock | Mock HTTP 请求 |
| BeautifulSoup4 | HTML 解析（验证提取结果） |

---

## 七、测试输出验证

### 7.1 预期输出格式

```
========================================
网页内容摘要
========================================
URL: https://example.com/article
标题: 示例文章标题
========================================
摘要:
这是生成的 100-300 字摘要内容，准确概括了网页的主要信息。
========================================
耗时: 5.2s
```

### 7.2 验证要点

| 验证项 | 验证方法 |
| --- | --- |
| URL | 检查是否与输入一致 |
| 标题 | 检查是否与网页 &lt;title&gt; 一致 |
| 摘要长度 | 检查是否在 100-300 字之间 |
| 摘要质量 | 人工检查是否准确概括网页内容 |
| 耗时 | 检查是否大于 0 |
