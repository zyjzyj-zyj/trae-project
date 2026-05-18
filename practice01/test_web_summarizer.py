import pytest
import os
import sys
import yaml
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))
import web_summarizer


class TestLoadConfig:
    def test_load_config_file_not_exists(self):
        config = web_summarizer.load_config('nonexistent.yaml')
        assert config['model_type'] == 'mock'
        assert config['max_tokens'] == 300
    
    def test_load_config_normal(self, tmp_path):
        config_file = tmp_path / 'test_config.yaml'
        config_file.write_text('''
model_type: qwen
model_path: /test/models/
max_tokens: 500
timeout: 60
''')
        config = web_summarizer.load_config(str(config_file))
        assert config['model_type'] == 'qwen'
        assert config['model_path'] == '/test/models/'
        assert config['max_tokens'] == 500
        assert config['timeout'] == 60
    
    def test_load_config_invalid_yaml(self, tmp_path):
        config_file = tmp_path / 'invalid_config.yaml'
        config_file.write_text('invalid: yaml: content')
        with pytest.raises(ValueError, match='配置文件格式错误'):
            web_summarizer.load_config(str(config_file))
    
    def test_load_config_partial(self, tmp_path):
        config_file = tmp_path / 'partial_config.yaml'
        config_file.write_text('model_type: llama')
        config = web_summarizer.load_config(str(config_file))
        assert config['model_type'] == 'llama'
        assert config['max_tokens'] == 300


class TestExtractContent:
    def test_extract_content_normal(self):
        html = '''
        <!DOCTYPE html>
        <html>
        <head><title>测试</title></head>
        <body>
            <nav>导航</nav>
            <script>alert(1)</script>
            <h1>标题</h1>
            <p>正文内容</p>
            <footer>页脚</footer>
        </body>
        </html>
        '''
        content = web_summarizer.extract_content(html)
        assert '导航' not in content
        assert 'alert' not in content
        assert '页脚' not in content
        assert '标题' in content
        assert '正文内容' in content
    
    def test_extract_content_remove_script(self):
        html = '<script>var x = 1;</script><p>正文</p>'
        content = web_summarizer.extract_content(html)
        assert 'var x = 1' not in content
        assert '正文' in content
    
    def test_extract_content_remove_nav(self):
        html = '<nav>导航</nav><p>正文</p>'
        content = web_summarizer.extract_content(html)
        assert '导航' not in content
        assert '正文' in content
    
    def test_extract_content_remove_footer(self):
        html = '<p>正文</p><footer>页脚</footer>'
        content = web_summarizer.extract_content(html)
        assert '页脚' not in content
        assert '正文' in content
    
    def test_extract_content_empty(self):
        content = web_summarizer.extract_content('')
        assert content == ''


class TestMockModel:
    def test_mock_model_generate(self):
        model = web_summarizer.MockModel()
        summary = model.generate('测试内容', max_tokens=300)
        assert len(summary) > 0
        assert '模拟' in summary


class TestLoadModel:
    def test_load_model_mock(self):
        model = web_summarizer.load_model('mock', './models/')
        assert isinstance(model, web_summarizer.MockModel)
    
    def test_load_model_unsupported(self):
        with pytest.raises(ValueError, match='不支持的模型类型'):
            web_summarizer.load_model('invalid', './models/')


class TestGenerateSummary:
    def test_generate_summary_normal(self):
        model = web_summarizer.MockModel()
        summary = web_summarizer.generate_summary(model, '这是测试内容，用于测试摘要生成功能。', 300)
        assert len(summary) > 0
    
    def test_generate_summary_empty_content(self):
        model = web_summarizer.MockModel()
        summary = web_summarizer.generate_summary(model, '', 300)
        assert '无法生成摘要' in summary


class TestPrintResults:
    def test_print_results_normal(self, capsys):
        web_summarizer.print_results(
            'https://example.com',
            '测试标题',
            '这是测试摘要',
            5.2
        )
        captured = capsys.readouterr()
        assert 'https://example.com' in captured.out
        assert '测试标题' in captured.out
        assert '这是测试摘要' in captured.out
        assert '5.2s' in captured.out


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
