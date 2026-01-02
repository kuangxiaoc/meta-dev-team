# src/meta_dev_team/app.py
import chainlit as cl
from meta_dev_team.main import build_graph

# 初始化 Graph
# 我们在 chat 开始时构建一次图
@cl.on_chat_start
async def start():
    app = build_graph()
    cl.user_session.set("app", app)
    
    await cl.Message(
        content="👋 欢迎来到 Meta-Dev-Team！\n我是你的自动化开发团队。请告诉我你想做一个什么工具？\n\n(例如：写一个 Python 脚本，扫描当前目录下所有 .txt 文件并统计行数)"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    app = cl.user_session.get("app")
    
    inputs = {"requirement": message.content}
    
    # 发送一个空的最终消息，准备填充
    final_response = await cl.Message(content="正在召集 Agent 团队工作...").send()
    
    # 使用 astream (异步流) 来获取每一步的执行结果
    # config runnable_config 用于传递递归限制等
    async for output in app.astream(inputs, config={"recursion_limit": 10}):
        
        # output 是一个字典，key 是节点名，value 是该节点的输出状态更新
        for node_name, state_update in output.items():
            
            if node_name == "product_manager":
                async with cl.Step(name="Product Manager (PM)") as step:
                    step.input = "分析需求..."
                    step.output = state_update['plan']
            
            elif node_name == "coder":
                async with cl.Step(name="Coder (工程师)") as step:
                    step.input = "正在编写/修复代码..."
                    code = state_update['code']
                    step.output = f"```python\n{code}\n```"
                    
                    # 实时更新最终消息，让用户看到最新的代码
                    final_response.content = f"### 最新生成的代码\n```python\n{code}\n```"
                    await final_response.update()

            elif node_name == "reviewer":
                async with cl.Step(name="Reviewer (测试员)") as step:
                    feedback = state_update.get('review_feedback', 'PASS')
                    if "PASS" in feedback:
                        step.output = "✅ 测试通过！"
                    else:
                        step.output = f"❌ 发现问题:\n{feedback}"
                        step.is_error = True

    # 循环结束后，更新最终状态
    final_response.content += "\n\n✅ **开发任务完成！**"
    await final_response.update()