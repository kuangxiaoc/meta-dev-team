import docker
import os
import tempfile
import shutil
from typing import Dict, Tuple

class DockerSandbox:
    def __init__(self, image="python:3.10-slim"):
        self.client = docker.from_env()
        self.image = image

    def run_project(self, files: Dict[str, str], entry_point: str = "main.py") -> str:
        """
        在 Docker 中运行多文件项目
        :param files: 文件名到内容的字典
        :param entry_point: 入口文件
        :return: 运行日志 (stdout + stderr)
        """
        # 1. 创建宿主机临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 2. 将文件写入临时目录
            for filename, content in files.items():
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            
            # 3. 准备 Docker 运行命令
            # 如果有 requirements.txt，先安装依赖
            command_list = []
            if "requirements.txt" in files:
                # 使用阿里云镜像源加速
                command_list.append("pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/")
            
            if entry_point in files:
                command_list.append(f"python {entry_point}")
            else:
                return f"Error: Entry point '{entry_point}' not found in generated files."

            # 组合命令: sh -c "cmd1 && cmd2"
            full_command = " && ".join(command_list)
            
            try:
                print(f"--- [Sandbox] Starting Container in {temp_dir} ---")
                # 4. 运行容器
                # remove=True: 运行完自动删除容器
                # volumes: 挂载临时目录到容器内的 /app
                # working_dir: 设置工作目录
                # network_mode: 'host' 或者允许联网 (默认bridge通常可以联网，除非配置了限制)
                logs = self.client.containers.run(
                    image=self.image,
                    command=f'/bin/sh -c "{full_command}"',
                    volumes={temp_dir: {'bind': '/app', 'mode': 'rw'}},
                    working_dir="/app",
                    remove=True,
                    network_mode="bridge" # 确保能联网 pip install
                )
                return logs.decode("utf-8")
                
            except docker.errors.ContainerError as e:
                # 容器内命令执行返回非0退出码
                return f"Runtime Error:\n{e.stderr.decode('utf-8') if e.stderr else str(e)}"
            except Exception as e:
                return f"Docker Infrastructure Error: {str(e)}"

# 单例测试
if __name__ == "__main__":
    sandbox = DockerSandbox()
    res = sandbox.run_project({
        "main.py": "import utils; print(utils.add(1, 2))",
        "utils.py": "def add(a, b): return a + b"
    })
    print(res)