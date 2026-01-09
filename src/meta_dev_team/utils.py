# src/meta_dev_team/utils.py
import re
from typing import Dict

def parse_multi_file_code(text: str) -> Dict[str, str]:
    """
    解析 LLM 返回的文本，提取多个文件。
    约定格式:
    ## file: main.py
    ```python
    print("hello")
    ```
    ## file: requirements.txt
    requests
    """
    files = {}
    
    # 正则匹配: 找到 "## file: filename" 及其后的内容
    # (?s) 开启 dotall 模式
    pattern = r"##\s*file:\s*([a-zA-Z0-9_\-\.]+)\n(.*?)((?=##\s*file:)|$)"
    matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
    for match in matches:
        filename = match.group(1).strip()
        filecontent = match.group(2).strip()
        # 清洗 content 中的 markdown 标记
        code_block_pattern = r"```(?:\w+)?\n(.*?)```"
        code_match = re.search(code_block_pattern, filecontent, re.DOTALL)
        if code_match:
            filecontent = code_match.group(1).strip()

        files[filename] = filecontent

        # 如果没匹配到任何特定格式，但有代码块，做个容错，默认存为 main.py
    if not files:
        code_block_pattern = r"```(?:\w+)?\n(.*?)```"
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            files["main.py"] = match.group(1).strip()
            
    return files
