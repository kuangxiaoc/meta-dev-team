# src/meta_dev_team/main.py
from langgraph.graph import StateGraph, START, END
from meta_dev_team.state import AgentState
from meta_dev_team.nodes import product_manager_node, coder_node

def build_graph():
    # 1. 创建 StateGraph
    workflow = StateGraph(AgentState)

    # 2. 添加节点 (Nodes)
    # add_node("节点名称", 函数)
    workflow.add_node("product_manager", product_manager_node)
    workflow.add_node("coder", coder_node)

    # 3. 添加连线 (Edges)
    # START -> PM
    workflow.add_edge(START, "product_manager")
    
    # PM -> Coder
    workflow.add_edge("product_manager", "coder")
    
    # Coder -> END (结束)
    workflow.add_edge("coder", END)

    # 4. 编译图 (Compile)
    app = workflow.compile()
    return app

def main():
    # 获取图实例
    app = build_graph()
    
    # 模拟用户输入
    user_input = input("请输入你的需求 (例如: 帮我写一个贪吃蛇游戏): ")
    if not user_input:
        user_input = "使用 Python 写一个计算斐波那契数列的脚本，并打印前10个数。"

    print(f"开始执行任务: {user_input}")

    # 运行图
    initial_state = {"requirement": user_input}
    
    # invoke 会执行整个流程
    result = app.invoke(initial_state)

    print("\n================ 最终结果 ================")
    print(f"PM 的计划:\n{result.get('plan')}")
    print("\n----------------------------------------")
    print(f"Coder 的代码:\n{result.get('code')}")
    print("==========================================")

if __name__ == "__main__":
    main()