import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from tools import search,fetch_url
from deepagents.backends import FilesystemBackend

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from skills import SkillsMiddleware
from shell import ShellMiddleware
# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Load environment ===
load_dotenv()

# === Config ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL =  "doubao-seed-1-8-251215"
RECURSION_LIMIT = int(os.getenv("RECURSION_LIMIT", 25))

# === 系统指令 ===
SYSTEM_PROMPT = """你是拥有多种技能的智能体，能够帮助用户完成各种任务。

## 工作流程
1. 理解用户需求。
2. 首先考虑已安装的技能来满足需求，并根据需要调用工具。
3. 如果没有合适的技能，考虑直接使用工具来完成任务。

## 输出要求
- 使用中文输出

## 严格遵循
- 凡是生成与写入的文件，默认必须放在/fs/ 目录下
"""

logging.info("✅ 系统指令已加载")

def make_backend(runtime):
    return CompositeBackend(
        default=FilesystemBackend(),  
        routes={
            "/fs/": FilesystemBackend(root_dir="./fs",virtual_mode=True),
            "/memories/": StoreBackend(runtime) 
        }
    )

# === 创建模型实例 ===
model = ChatOpenAI(
    model=OPENAI_MODEL,
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)

# === Skills 配置 ===
USER_SKILLS_DIR = Path.home() / ".deepagents" / "agent" / "skills"
WORKSPACE_ROOT = str(Path(__file__).parent.resolve())

skills_middleware = SkillsMiddleware(
    skills_dir=USER_SKILLS_DIR,
    assistant_id="agent",
    project_skills_dir=None,
)

# === Shell 中间件配置 ===
shell_middleware = ShellMiddleware(
    workspace_root=WORKSPACE_ROOT,
    timeout=120.0,
    max_output_bytes=100000,
)

logging.info(f"✅ Skills 中间件已配置")
logging.info(f"  - 用户 Skills 目录: {USER_SKILLS_DIR}")
logging.info(f"✅ Shell 中间件已配置")
logging.info(f"  - 工作目录: {WORKSPACE_ROOT}")

# === 创建 DeepAgent（无后端，无子智能体）===
# 注意：在 langgraph dev 模式下，store 由平台自动提供，不需要手动传入

research_subagent = {
    "name": "search-agent",
    "description": "使用search工具进行信息检索与总结的智能体",
    "system_prompt": "你是web检索与研究智能体。",
    "tools": [search,fetch_url],
    "model":model 
}

agent = create_deep_agent(
    model=model,
    tools=[],
    subagents=[research_subagent],
    backend=make_backend,
    middleware=[skills_middleware, shell_middleware],
    system_prompt=SYSTEM_PROMPT,debug=True
).with_config({"recursion_limit": RECURSION_LIMIT})

logging.info(f"✅ 简单 DeepAgent 已创建")
logging.info(f"  - 模型: {OPENAI_MODEL}")
logging.info(f"  - 递归限制: {RECURSION_LIMIT}")

# === 测试运行 ===
if __name__ == "__main__":
    import sys
    
    # 从命令行获取股票代码，如果没有则使用默认值
    stock_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "分析贵州茅台 600519"
    
    logging.info(f"\n{'='*60}")
    logging.info(f"开始分析: {stock_query}")
    logging.info(f"{'='*60}\n")
    
    try:
        # 运行 agent
        result = agent.invoke({"messages": [{"role": "user", "content": stock_query}]})
        
        # 输出结果
        print("\n" + "="*60)
        print("分析结果：")
        print("="*60 + "\n")
        
        # 获取最后一条消息
        if result and "messages" in result:
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                print(last_message.content)
            else:
                print(last_message)
        else:
            print("未获取到分析结果")
            
    except Exception as e:
        logging.error(f"分析过程中出错: {str(e)}", exc_info=True)
