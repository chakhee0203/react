import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def get_llm():
    ds_key = os.environ.get("DEEPSEEK_API_KEY")
    zhipu_key = os.environ.get("ZHIPU_API_KEY")
    if ds_key:
        return ChatOpenAI(
            model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=ds_key,
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            temperature=0,
        )
    if zhipu_key:
        return ChatOpenAI(
            model=os.environ.get("ZHIPU_MODEL", "glm-4-flash"),
            api_key=zhipu_key,
            base_url=os.environ.get("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"),
            temperature=0,
        )
    raise RuntimeError("Missing API Key: 请在侧边栏或 .env 中配置 DEEPSEEK_API_KEY 或 ZHIPU_API_KEY")
