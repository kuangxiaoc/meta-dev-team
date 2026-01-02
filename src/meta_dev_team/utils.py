# src/meta_dev_team/utils.py
import re

def clean_code(code_text: str) -> str:
    """
    清洗 LLM 输出的代码，去除 Markdown 标记
    """
    # 匹配 ```python ... ``` 或者 ``` ... ```
    pattern = r"```(?:python)?\n(.*?)```"
    match = re.search(pattern, code_text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # 如果没有 markdown 标记，假设整个文本就是代码，但在生产环境中这比较危险
    # 这里做一个简单的容错
    return code_text.strip()