import argparse
import time
import os
import re
import yaml
import requests
from bs4 import BeautifulSoup
from typing import Dict, Tuple, Optional

CONFIG_PATH = 'config.yaml'
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_TOKENS = 300
MIN_SUMMARY_LENGTH = 100
MAX_SUMMARY_LENGTH = 300


class MockModel:
    def __init__(self):
        pass
    
    def generate(self, prompt: str, max_tokens: int = 300) -> str:
        time.sleep(0.5)
        return "这是一个模拟的摘要内容，用于演示程序的工作流程。在实际使用时，请配置真实的本地模型（如 Llama、Qwen 或 ChatGLM）来生成准确的摘要。这个模拟摘要长度适中，大约在 100-300 字之间，符合用户的需求。"


def load_config(config_path: str) -> Dict:
    default_config = {
        'model_type': 'mock',
        'model_path': './models/',
        'max_tokens': 300,
        'timeout': 30
    }
    
    if not os.path.exists(config_path):
        return default_config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            file_config = yaml.safe_load(f) or {}
        
        config = {**default_config, **file_config}
        return config
    except yaml.YAMLError:
        raise ValueError("配置文件格式错误")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='网页内容摘要工具')
    parser.add_argument('--url', required=True, help='网页 URL')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--model-type', help='模型类型 (llama/qwen/chatglm/mock)')
    parser.add_argument('--model-path', help='模型路径')
    return parser.parse_args()


def fetch_webpage(url: str, timeout: int) -> Tuple[str, str]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        html_content = response.text
        
        soup = BeautifulSoup(html_content, 'lxml')
        title_tag = soup.find('title')
        page_title = title_tag.get_text(strip=True) if title_tag else ''
        
        return (html_content, page_title)
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"网络请求失败: {e}")


def extract_content(html_content: str) -> str:
    if not html_content:
        return ''
    
    soup = BeautifulSoup(html_content, 'lxml')
    
    for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
        element.decompose()
    
    for element in soup.find_all(class_=re.compile(r'ad|advertisement|banner|sidebar', re.I)):
        element.decompose()
    
    text_parts = []
    for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = tag.get_text(strip=True)
        if text:
            text_parts.append(text)
    
    content = ' '.join(text_parts)
    content = re.sub(r'\s+', ' ', content).strip()
    
    return content


def load_model(model_type: str, model_path: str) -> object:
    if model_type == 'mock':
        return MockModel()
    elif model_type == 'llama':
        raise NotImplementedError("Llama 模型支持尚未实现，请使用 mock 模型进行测试")
    elif model_type == 'qwen':
        raise NotImplementedError("Qwen 模型支持尚未实现，请使用 mock 模型进行测试")
    elif model_type == 'chatglm':
        raise NotImplementedError("ChatGLM 模型支持尚未实现，请使用 mock 模型进行测试")
    else:
        raise ValueError(f"不支持的模型类型: {model_type}")


def generate_summary(model: object, content: str, max_tokens: int) -> str:
    if not content:
        return "无法生成摘要：没有提取到有效的正文内容。"
    
    prompt = f"""请为以下内容生成一段 100-300 字的摘要：

{content}

摘要："""
    
    summary = model.generate(prompt, max_tokens=max_tokens)
    return summary


def print_results(url: str, title: str, summary: str, elapsed_time: float):
    print("=" * 40)
    print("网页内容摘要")
    print("=" * 40)
    print(f"URL: {url}")
    print(f"标题: {title}")
    print("=" * 40)
    print("摘要:")
    print(summary)
    print("=" * 40)
    print(f"耗时: {elapsed_time:.1f}s")


def main():
    try:
        start_time = time.time()
        
        args = parse_args()
        config = load_config(args.config)
        
        if args.model_type:
            config['model_type'] = args.model_type
        if args.model_path:
            config['model_path'] = args.model_path
        
        print("正在抓取网页...")
        html_content, page_title = fetch_webpage(args.url, config['timeout'])
        
        print("正在提取正文...")
        content = extract_content(html_content)
        
        print("正在加载模型...")
        model = load_model(config['model_type'], config['model_path'])
        
        print("正在生成摘要...")
        summary = generate_summary(model, content, config['max_tokens'])
        
        elapsed_time = time.time() - start_time
        
        print_results(args.url, page_title, summary, elapsed_time)
    
    except Exception as e:
        print(f"错误: {e}")


if __name__ == '__main__':
    main()
