# src/meta_dev_team/main.py
from langgraph.graph import StateGraph, START, END
from meta_dev_team.state import AgentState
from meta_dev_team.nodes import product_manager_node, coder_node, reviewer_node

# 定义路由逻辑
def should_continue(state: AgentState):
    feedback = state.get("review_feedback", "")
    count = state.get("iteration_count", 0)
    
    # 1. 如果 Reviewer 说 PASS，则结束
    if "PASS" in feedback:
        return "end"
    
    # 2. 如果循环超过 3 次，强制结束（避免死循环耗干 Token）
    if count >= 3:
        print("--- [系统] 达到最大重试次数，强制结束 ---")
        return "end"
    
    # 3. 否则，回炉重造
    return "rewrite"

def build_graph():
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("product_manager", product_manager_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("reviewer", reviewer_node)

    # 建立主流程
    workflow.add_edge(START, "product_manager")
    workflow.add_edge("product_manager", "coder")
    workflow.add_edge("coder", "reviewer")

    # 添加条件边
    # 从 reviewer 节点出发，根据 should_continue 的返回值决定去向
    workflow.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "rewrite": "coder", # 如果返回 rewrite，走 coder
            "end": END          # 如果返回 end，结束
        }
    )

    return workflow.compile()

def main():
    app = build_graph()
    
    # 故意给一个稍微复杂的需求，容易让初版代码出错
    default_prompt = "写一个 Python 脚本，通过 requests 库爬取 example.com 的标题，并保存到 CSV 文件中。要注意处理异常。"
    
    user_input = input(f"请输入需求 (默认: {default_prompt}): ") or default_prompt

    print(f"开始执行任务: {user_input}")

    # 递归限制设高一点，因为我们要循环
    result = app.invoke({"requirement": user_input}, config={"recursion_limit": 10})

    print("\n================ 最终交付代码 ================")
    print(result.get('code'))
    print("==============================================")

if __name__ == "__main__":
    main()