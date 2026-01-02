# src/meta_dev_team/nodes.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from meta_dev_team.state import AgentState

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
    """
    PM 节点：负责分析需求
    """
    print(f"\n--- [PM] 正在分析需求: {state['requirement']} ---")
    
    system_prompt = "你是一位资深产品经理。请根据用户的需求，编写一份简短清晰的开发计划（Spec）。包含核心功能点即可。"
    user_prompt = f"需求：{state['requirement']}"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm.invoke(messages)
    
    # 返回更新的状态：更新 'plan' 初始化计数器
    return {"plan": response.content,"interation_count":0}

def coder_node(state: AgentState):
    """
    Coder 节点：负责写代码
    """
    plan = state['plan']
    feedback = state.get('review_feedback')
    if feedback:
        print(f"\n--- [Coder] 收到反馈，正在修复代码 (第 {state['iteration_count'] + 1} 次迭代) ---")
        system_prompt = "你是高级Python工程师。根据审查反馈修复代码。只输出完整的修正后代码。"
        user_prompt = f"原代码：\n{state['code']}\n\n审查反馈：{feedback}"
    else:
        print(f"\n--- [Coder] 正在编写代码 ---")
        system_prompt = "您是一位精英python程序员。您接收项目想法，并输出安全且可组合的代码。您始终使用最新的技术和最佳实践。深呼吸，逐步思考如何使用以下步骤最佳地完成这个目标。不需要markdown的解释"
        user_prompt = f"开发计划：\n{plan}"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm.invoke(messages)
    
    # 返回更新的状态：更新 'code' 并增加计数
    return {"code": response.content,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "review_feedback": None # 修复后清除旧反馈
          }


def reviewer_node(state: AgentState):
    """
    Reviewer 节点：模拟代码审查
    """
    print(f"\n--- [Reviewer] 正在审查代码 ---")
    code = state['code']
    
    # 这里我们模拟一个挑剔的审查员
    # 提示词技巧：要求它在通过时必须只输出 "PASS"
    system_prompt = """
    你是代码审查员。检查代码是否有明显的逻辑错误、缺少 import 或不符合需求。
    如果代码看起来没问题，请**仅**输出 "PASS"。
    如果代码有问题，请简短列出修改建议。
    """
    
    user_prompt = f"待审查代码：\n{code}"
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    
    feedback = response.content
    if "PASS" in feedback:
        print(">>> 审查通过！")
    else:
        print(f">>> 发现问题: {feedback}")
        
    return {"review_feedback": feedback}