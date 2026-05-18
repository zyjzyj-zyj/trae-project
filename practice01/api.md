# 网页内容摘要工具 - API 设计文档

## 一、模块结构

```
web_summarizer.py
    ├── load_config()          # 加载配置
    ├── parse_args()           # 解析命令行参数
    ├── fetch_webpage()        # 抓取网页
    ├── extract_content()      # 提取正文
    ├── load_model()           # 加载本地模型
    ├── generate_summary()     # 生成摘要
    ├── print_results()        # 输出结果
    └── main()                 # 主入口
```

---

## 二、全局变量

| 变量名 | 类型 | 说明 |
| --- | --- | --- |
| `CONFIG_PATH` | str | 配置文件路径，固定为 `config.yaml` |
| `DEFAULT_TIMEOUT` | int | 默认超时时间，30 秒 |
| `DEFAULT_MAX_TOKENS` | int | 默认最大 token 数，300 |
| `MIN_SUMMARY_LENGTH` | int | 摘要最小长度，100 字 |
| `MAX_SUMMARY_LENGTH` | int | 摘要最大长度，300 字 |

---

## 三、方法详细设计

### 3.1 `load_config(config_path: str) -> dict`

**功能**：从指定路径读取并解析 YAML 配置文件

**参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `config_path` | str | 配置文件路径 |

**返回值**：
| 类型 | 说明 |
| --- | --- |
| `dict` | 包含配置参数的字典 |

**异常处理**：
- 文件不存在：使用默认配置
- 解析错误：抛出 `ValueError`

**伪代码**：
```plaintext
FUNCTION load_config(config_path):
    default_config = {
        'model_type': 'qwen',
        'model_path': './models/',
        'max_tokens': 300,
        'timeout': 30
    }
    
    IF 文件不存在 config_path:
        返回 default_config
    
    尝试读取并解析 YAML 文件:
        config = 合并 default_config 和文件配置
        返回 config
    EXCEPT 解析错误:
        抛出 ValueError("配置文件格式错误")
```

---

### 3.2 `parse_args() -> argparse.Namespace`

**功能**：解析命令行参数

**参数**：无

**返回值**：
| 类型 | 说明 |
| --- | --- |
| `argparse.Namespace` | 包含命令行参数的对象 |

**支持参数**：
| 参数 | 说明 | 必填 |
| --- | --- | --- |
| `--url` | 网页 URL | 是 |
| `--config` | 配置文件路径 | 否 |
| `--model-type` | 模型类型 | 否 |
| `--model-path` | 模型路径 | 否 |

**伪代码**：
```plaintext
FUNCTION parse_args():
    parser = 创建 ArgumentParser
    parser.add_argument('--url', required=True, help='网页 URL')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--model-type', help='模型类型 (llama/qwen/chatglm)')
    parser.add_argument('--model-path', help='模型路径')
    返回 parser.parse_args()
```

---

### 3.3 `fetch_webpage(url: str, timeout: int) -> tuple`

**功能**：抓取网页内容

**参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `url` | str | 网页 URL |
| `timeout` | int | 超时时间（秒） |

**返回值**：
| 类型 | 说明 |
| --- | --- |
| `tuple` | `(html_content, page_title)` |

**异常处理**：
- 网络错误：抛出 `ConnectionError`
- HTTP 错误：抛出 `HTTPError`

**伪代码**：
```plaintext
FUNCTION fetch_webpage(url, timeout):
    发送 HTTP GET 请求到 url，设置超时时间
    IF 状态码 != 200:
        抛出 HTTPError(f"请求失败: {状态码}")
    
    html_content = 响应内容
    page_title = 从 HTML 中提取 <title> 标签内容
    返回 (html_content, page_title)
```

---

### 3.4 `extract_content(html_content: str) -> str`

**功能**：从 HTML 中提取正文内容

**参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `html_content` | str | HTML 内容 |

**返回值**：
| 类型 | 说明 |
| --- | --- |
| `str` | 提取的正文文本 |

**伪代码**：
```plaintext
FUNCTION extract_content(html_content):
    使用 HTML 解析器解析 html_content
    移除 script、style、nav、footer、aside 等标签
    移除广告相关元素
    提取所有 p、h1-h6 标签的文本内容
    合并文本，去除多余空白
    返回正文内容
```

---

### 3.5 `load_model(model_type: str, model_path: str) -> object`

**功能**：加载本地模型

**参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `model_type` | str | 模型类型 (llama/qwen/chatglm) |
| `model_path` | str | 模型路径 |

**返回值**：
| 类型 | 说明 |
| --- | --- |
| `object` | 模型对象 |

**伪代码**：
```plaintext
FUNCTION load_model(model_type, model_path):
    IF model_type == 'llama':
        使用 Llama 库加载模型
    ELIF model_type == 'qwen':
        使用 Qwen 库加载模型
    ELIF model_type == 'chatglm':
        使用 ChatGLM 库加载模型
    ELSE:
        抛出 ValueError(f"不支持的模型类型: {model_type}")
    
    返回模型对象
```

---

### 3.6 `generate_summary(model: object, content: str, max_tokens: int) -> str`

**功能**：使用模型生成摘要

**参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `model` | object | 模型对象 |
| `content` | str | 正文内容 |
| `max_tokens` | int | 最大 token 数 |

**返回值**：
| 类型 | 说明 |
| --- | --- |
| `str` | 生成的摘要 |

**伪代码**：
```plaintext
FUNCTION generate_summary(model, content, max_tokens):
    prompt = f"""请为以下内容生成一段 100-300 字的摘要：

{content}

摘要："""
    
    summary = model.generate(prompt, max_tokens=max_tokens)
    返回 summary
```

---

### 3.7 `print_results(url: str, title: str, summary: str, elapsed_time: float)`

**功能**：格式化输出结果

**参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `url` | str | 网页 URL |
| `title` | str | 网页标题 |
| `summary` | str | 摘要内容 |
| `elapsed_time` | float | 耗时（秒） |

**返回值**：无

**输出格式**：
```
========================================
网页内容摘要
========================================
URL: https://example.com/article
标题: 示例文章标题
========================================
摘要:
这是生成的摘要内容...
========================================
耗时: 5.2s
```

**伪代码**：
```plaintext
FUNCTION print_results(url, title, summary, elapsed_time):
    打印 "========================================"
    打印 "网页内容摘要"
    打印 "========================================"
    打印 f"URL: {url}"
    打印 f"标题: {title}"
    打印 "========================================"
    打印 "摘要:"
    打印 summary
    打印 "========================================"
    打印 f"耗时: {elapsed_time:.1f}s"
```

---

### 3.8 `main()`

**功能**：主程序入口，协调整个流程

**执行流程**：
1. 解析命令行参数
2. 加载配置
3. 抓取网页
4. 提取正文内容
5. 加载模型
6. 生成摘要
7. 输出结果

**伪代码**：
```plaintext
FUNCTION main():
    TRY:
        记录开始时间
        
        args = parse_args()
        config = load_config(args.config)
        
        合并命令行参数到 config
        
        打印 "正在抓取网页..."
        html_content, page_title = fetch_webpage(args.url, config['timeout'])
        
        打印 "正在提取正文..."
        content = extract_content(html_content)
        
        打印 "正在加载模型..."
        model = load_model(config['model_type'], config['model_path'])
        
        打印 "正在生成摘要..."
        summary = generate_summary(model, content, config['max_tokens'])
        
        elapsed_time = 当前时间 - 开始时间
        
        print_results(args.url, page_title, summary, elapsed_time)
    
    EXCEPT Exception AS e:
        打印 f"错误: {e}"
```

---

## 四、数据流转图

```
命令行参数
    ↓
parse_args() → args
    ↓
load_config() → config
    ↓
fetch_webpage(url, timeout) → html_content, page_title
    ↓
extract_content(html_content) → content
    ↓
load_model(model_type, model_path) → model
    ↓
generate_summary(model, content, max_tokens) → summary
    ↓
print_results() → 控制台输出
```
