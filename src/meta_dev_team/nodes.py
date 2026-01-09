# src/meta_dev_team/nodes.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from meta_dev_team.state import AgentState
from langchain_experimental.utilities import PythonREPL
from meta_dev_team.utils import parse_multi_file_code
from meta_dev_team.sandbox import DockerSandbox
# 1. 加载环境变量
load_dotenv()

# 2. 初始化 LLM
# 
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "qwen-plus"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_API_BASE"),
    temperature=0.2, # 写代码需要低温度以保证精确
)

# --- 节点定义 ---

def product_manager_node(state: AgentState):
    print(f"\n--- [PM] 分析需求 ---")
    # 更新 Prompt，强调文件结构
    system_prompt = """你是一位资深技术架构师。
    请根据用户需求，设计一份详细的【开发计划】。
    
    必须明确规划以下内容：
    1. 需要创建哪些文件（文件名必须包含扩展名）。
    2. 每个文件的核心职责（例如：main.py 负责调度，utils.py 负责核心逻辑）。
    3. 涉及到的第三方库（生成 requirements.txt 内容）。
    
    请确保计划具备可执行性，不要只给笼统的建议。"""

    user_prompt = f"需求：{state['requirement']}"
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    
    response = llm.invoke(messages)
    
    return {"plan": response.content, "iteration_count": 0}


def coder_node(state: AgentState):
    """
    Coder 节点：负责写代码
    """
    plan = state['plan']
    feedback = state.get('review_feedback')
    
    # 核心修改：System Prompt 强制要求多文件格式
    format_instruction = """
    【输出格式严格要求】
    请你将代码拆分为多个文件，并严格按照以下格式输出（不要使用 Markdown 代码块包裹整个输出，而是针对每个文件单独包裹）：

    ## file: <filename>
    ```python
    <file_content>
    ```

    【示例结构参考】（注意：以下仅为格式示例，**绝对不要**抄袭里面的代码逻辑！）
    
    ## file: requirements.txt
    requests
    pandas
    
    ## file: utils.py
    ```python
    # 这是一个格式示例，请根据实际需求编写真实逻辑
    def real_function():
        pass
    ```
    """
    base_instruction = f"""
    你是 Python 专家工程师。请根据【开发计划】或【审查反馈】编写代码。
    
    ⚠️ **重要指令**：
    1. **必须** 严格遵循【开发计划】中的业务逻辑（例如：如果要求爬虫，必须使用 requests/BeautifulSoup 等；如果要求 CSV，必须用 pandas/csv）。
    2. **禁止** 使用 "Hello World" 或 "pass" 等占位符代码，必须写出完整可运行的逻辑。
    3. 必须输出 `requirements.txt` 以处理依赖。
    
    {format_instruction}
    """
    if feedback:
        print(f"\n--- [Coder] 修复代码 (Round {state['iteration_count'] + 1}) ---")
        user_prompt = f"""
        【任务目标】：根据审查反馈修复代码。
        
        【上次代码反馈】：
        {feedback}
        
        请重写所有受影响的文件。
        """
    else:
        print(f"\n--- [Coder] 编写代码 ---")
        user_prompt = f"""
        【任务目标】：根据开发计划编写代码。
        
        【开发计划】：
        {plan}
        """
    
    messages = [SystemMessage(content=base_instruction), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    files = parse_multi_file_code(response.content)
    
    return {
        "files": files,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "review_feedback": None
    }

    
def reviewer_node(state: AgentState):
    print(f"\n--- [Reviewer] Docker 环境运行测试 ---")
    
    files = state.get('files', {})
    if not files:
        return {"review_feedback": "❌ Error: Coder 没有生成任何有效的文件格式。请检查输出格式。"}

    # 初始化沙箱
    sandbox = DockerSandbox() # 默认 python:3.10-slim
    
    # 运行
    result = sandbox.run_project(files, entry_point="main.py")
    
    print(f">>> Docker 输出:\n{result}")

    # 简单的判错逻辑
    if "Traceback" in result or "Error" in result or "ModuleNotFoundError" in result:
        feedback = f"运行报错:\n{result}"
    else:
        feedback = "PASS"
        
    return {"review_feedback": feedback}