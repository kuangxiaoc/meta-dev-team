# src/meta_dev_team/app.py
from sys import displayhook
import chainlit as cl
from meta_dev_team.main import build_graph

# 定义 Chainlit 应用
@cl.on_chat_start
async def start():
    app = build_graph()
    cl.user_session.set("app", app)
    
    # 设置头像 (你可以找一个 SVG 放在 public 文件夹里)
    # await cl.Avatar(name="Meta-Dev-Team", path="public/anthropic.svg").send()
    # await cl.Avatar(name="User", path="public/user.svg").send()

    # Claude 风格的开场白通常非常简洁、客气
    welcome_message = """
    # Hello.
    
    我是 **Meta-Dev-Team**。
    我可以协助你进行全流程软件开发，包括需求分析、代码编写以及在安全环境中运行测试。
    
    请告诉我，今天你想构建什么？
    """
    
    await cl.Message(content=welcome_message).send()

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
                    files = state_update.get('files', {})
                    step.input = "编写项目工程..."

                    display_text= ""
                    for filename, content in files.items():
                        # 根据后缀名选择语言提示
                        lang = "python"
                        if filename.endswith(".txt"):
                            lang = "text"
                        elif filename.endswith(".json"):
                            lang = "json"
                            
                        display_text += f"### 📄 {filename}\n```{lang}\n{content}\n```\n\n"

                    step.output = display_text
                    #更新最终消息
                    final_response.content = f"### 📦 最新生成的工程文件\n{display_text}"
                    await final_response.update()

            elif node_name == "reviewer":
                async with cl.Step(name="Reviewer (Docker)") as step:
                    feedback = state_update.get('review_feedback', 'PASS')
                    if "PASS" in feedback:
                        step.output = "✅ Docker 测试通过！"
                    else:
                        step.output = f"❌ Docker 运行报错:\n{feedback}"
                        step.is_error = True


    # 循环结束后，更新最终状态
    final_response.content += "\n\n✅ **开发任务完成！**"
    await final_response.update()