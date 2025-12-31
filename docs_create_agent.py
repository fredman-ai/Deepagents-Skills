import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from skills import SkillsMiddleware
from shell import ShellMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import json
import uuid
from datetime import datetime
from langgraph.store.memory import InMemoryStore
from tongyi_patch import ChatTongyi
from langchain.agents.middleware.summarization import SummarizationMiddleware

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Load environment ===
os.environ["DASHSCOPE_API_KEY"] = "sk-b180144cb0a04dd982480c145fce6de4"

# === Config ===
RECURSION_LIMIT = int(os.getenv("RECURSION_LIMIT", 25))
WORKSPACE_ROOT = str(Path(__file__).parent.resolve())

# === 系统指令 ===
SYSTEM_PROMPT = """你是拥有多种文档处理技能的智能体，能够帮助用户完成各种类型的文档创建、分析和编辑任务。

## 工作流程
1. 理解用户需求。
2. 首先考虑已安装的技能来满足需求，并根据需要调用工具。如：处理docx文档，可以加载docx技能（docx skills）
3. 如果没有合适的技能，考虑直接使用工具来完成任务。

## 输出要求
- 使用中文输出

## 严格遵循
- 前工作目录 (CWD): {WORKSPACE_ROOT}
- 凡是生成与写入的文件，默认必须放在 ./fs/ 目录下。
- 如果使用 shell 工具解压文件，请使用绝对路径或明确的相对路径。
- 读取文件时，请使用绝对路径（如 {WORKSPACE_ROOT}/my_file.txt）以避免路径错误。
- **严禁使用 sudo 命令**。如果遇到权限问题，请停止并报告。
""".format(WORKSPACE_ROOT=WORKSPACE_ROOT)

logging.info("✅ 系统指令已加载")

def make_backend(runtime):
    return CompositeBackend(
        default=FilesystemBackend(),   ## 本地文件系统，可长期保存
        routes={
            "/fs/": FilesystemBackend(root_dir="./fs",virtual_mode=False),
            "/memories/": StoreBackend(runtime) 
        }
    )

# === 创建模型实例 ===
model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        max_tokens=None,
        max_retries=3,
        google_api_key="AIzaSyC6B5jbIaCYdM8u06uzWdEC5JZWginHtVw",
)

model2 = ChatTongyi(
    model="deepseek-v3",
    temperature=0.2,
    max_retries=3,
    # api_key is read from env DASHSCOPE_API_KEY automatically
)

# === Skills 配置 ===
USER_SKILLS_DIR = Path(WORKSPACE_ROOT) / "agent" / "skills"

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

# === 持久化配置 (Checkpointer) ===
# 使用 SQLite 保存对话上下文 (Memory)
DB_PATH = "checkpoints.sqlite"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn)
logging.info(f"✅ 持久化存储已配置: {DB_PATH}")

# === Store 持久化 (User Memories) ===
STORE_JSON_PATH = "store_memories.json"
store = InMemoryStore()

# 加载 Store
if os.path.exists(STORE_JSON_PATH):
    try:
        with open(STORE_JSON_PATH, "r", encoding="utf-8") as f:
            saved_items = json.load(f)
            for item in saved_items:
                store.put(item["namespace"], item["key"], item["value"])
        logging.info(f"✅ Store Memories 已加载: {STORE_JSON_PATH}")
    except Exception as e:
        logging.warning(f"⚠️ 加载 Store 失败: {e}")


# === 创建 DeepAgent（无后端，无子智能体）===

# === Summarization Middleware ===
summarization_middleware = SummarizationMiddleware(
    model=model2,
    trigger=("tokens", 5000),  # Trigger summarization at 5000 tokens to save cost
    keep=("messages", 4),      # Keep last 4 messages unsummarized
)

logging.info(f"✅ Summarization 中间件已配置 (Trigger: 5000 tokens)")

agent = create_deep_agent(
    model=model2,
    tools=[],
    # subagents=[research_subagent],
    backend=make_backend,
    middleware=[skills_middleware, shell_middleware, summarization_middleware],
    checkpointer=checkpointer,
    store=store,
    system_prompt=SYSTEM_PROMPT,debug=True
).with_config({"recursion_limit": RECURSION_LIMIT})

logging.info(f"✅ DeepAgents 已创建")
logging.info(f"  - 递归限制: {RECURSION_LIMIT}")

# === 测试运行 ===
if __name__ == "__main__":
    import sys
    
    # 从命令行获取股票代码，如果没有则使用默认值
    user_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "用read_file工具读取如下路径文档 /Users/infly2309/deepagents-skills/重庆啤酒（600132.SH）.docx ，删除文档中现有内容，并添加如下新文本：■医药工业增长稳健，受原材料上涨影响毛利率有所下降。 2023 年公司医药工业实现收入 110.79 亿元，同比增长 12.60%，实现毛利率 46.97%，受原材料成本上升影响下降 1.98pct。公司聚集大品种及精品战略取得成效，以安牛为代表的心脑血管业务实现营收 43.88 亿元，同比增长 8.02%，毛利率为 57.62%，下降 3.58pct；以六味地黄系列为代表的补益业务实现营收 17.30 亿元，同比增长 10.41%，毛利率为 37.39%，下降 5.60pct；清热类业务和妇科类业务实现营收 6.15 和 3.77 亿元，同比增长 16.10%和 8.16%，在成本压力下毛利率仍然实现了同比提升。"
    
    logging.info(f"\n{'='*60}")
    logging.info(f"开始分析: {user_query}")
    logging.info(f"{'='*60}\n")
    
    try:
        # 生成或指定会话 ID (Thread ID)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        logging.info(f"当前会话 ID: {thread_id}")

        # 运行 agent
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_query}]},
            config=config
        )
        
        # --- 持久化保存 Trajectory (便于评估) ---
        traj_dir = Path("trajectories")
        traj_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        traj_file = traj_dir / f"run_{timestamp}_{thread_id}.json"
        
        # 序列化处理 (处理非 JSON 可序列化对象)
        def default_serializer(obj):
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if hasattr(obj, "dict"):
                return obj.dict()
            return str(obj)

        with open(traj_file, "w", encoding="utf-8") as f:
            json.dump(result, f, default=default_serializer, ensure_ascii=False, indent=2)
            
        logging.info(f"✅ 轨迹已保存至: {traj_file}")
        
        # --- 保存 Store Memories ---
        try:
            # 获取所有存储项 (search all)
            items = store.search(["agent"]) # 假设主要使用 agent namespace，或使用空前缀
            # 如果 search([]) 不支持，通过 items 属性访问 (LangGraph 版本依赖)
            # 这里使用通用的 search 方法
            
            # 为了简单起见，我们列出所有 namespaces
            # 这里的实现依赖于 Store 的具体 API，langgraph 0.2+ search 支持 prefix
            all_items = store.search([])  # 获取所有
            
            serializable_items = []
            for item in all_items:
                serializable_items.append({
                    "namespace": item.namespace,
                    "key": item.key,
                    "value": item.value,
                    "created_at": str(item.created_at) if hasattr(item, "created_at") else None,
                    "updated_at": str(item.updated_at) if hasattr(item, "updated_at") else None
                })
            
            with open(STORE_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(serializable_items, f, ensure_ascii=False, indent=2)
            logging.info(f"✅ Store Memories 已保存: {STORE_JSON_PATH}")
            
        except Exception as e:
             # 如果 search([]) 失败，尝试 workaround 或忽略
             logging.warning(f"⚠️ 保存 Store 失败 (可能是 API 差异): {e}")
        # ---------------------------

        # 输出结果
        print("\n" + "="*60)
        print("处理结果：")
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