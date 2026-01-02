# src/meta_dev_team/state.py
from typing import TypedDict, List, Optional
from typing_extensions import Annotated
import operator

class AgentState(TypedDict):
    """
    Graph 的状态定义。
    所有的节点 (Nodes) 都会接收这个 State，并输出更新后的字段。
    """
    requirement: str                # 用户输入的原始需求
    plan: Optional[str]             # PM 生成的开发计划/Spec
    code: Optional[str]             # Coder 生成的代码
    messages: Annotated[List[dict], operator.add] # (可选) 这是一个追加型列表，用于保存对话历史
    review_feedback:Optional[str]   #代码审查意见
    iteration_count :int           # (新增) 循环次数，防止死循环