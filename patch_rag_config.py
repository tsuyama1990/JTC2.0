import re

with open("src/core/config.py", "r") as f:
    content = f.read()

replacement = """class RAGConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    base_dir: str = Field(default=".", description="Base directory for RAG operations to prevent path traversal")
    persist_dir: str = Field(default="./vector_store", description="Directory for RAG index")"""

content = content.replace('class RAGConfig(BaseSettings):\n    model_config = SettingsConfigDict(extra="ignore")\n    persist_dir: str = Field(default="./vector_store", description="Directory for RAG index")', replacement)

with open("src/core/config.py", "w") as f:
    f.write(content)
