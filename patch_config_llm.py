import re

with open("src/core/config.py", "r") as f:
    content = f.read()

diff = """<<<<<<< SEARCH
    tavily_api_key: SecretStr = Field(
        alias="TAVILY_API_KEY", description="Tavily Search API Key", min_length=20
    )
=======
    tavily_api_key: SecretStr = Field(
        alias="TAVILY_API_KEY", description="Tavily Search API Key", min_length=20
    )
    llm_model: str = Field(default="gpt-4o", description="LLM model name")
>>>>>>> REPLACE"""

with open("patch_config_llm.patch", "w") as f:
    f.write(diff)
