
with open("src/core/config.py") as f:
    content = f.read()

diff = r"""<<<<<<< SEARCH
    @field_validator("tavily_api_key")
    @classmethod
    def validate_tavily_key(cls, v: SecretStr) -> SecretStr:
        val = v.get_secret_value()
        if not val.startswith("tvly-"):
            if val != "dummy-tavily-key-long-enough-for-validation" and not val.startswith("sk-"):
                msg = "Tavily API Key must start with 'tvly-'"
                raise ValueError(msg)
        if len(val) < 20:
            msg = "Tavily API Key must be at least 20 characters long."
            raise ValueError(msg)

        import re
        key_pattern = re.compile(r"^[A-Za-z0-9_\-\.]+$")
        if not key_pattern.match(val):
            msg = "Tavily API Key contains invalid characters."
            raise ValueError(msg)

        if val != "dummy-tavily-key-long-enough-for-validation" and val != "sk-dummy-test-key-long-enough-for-validation" and not getattr(cls, "_bypass_network_validation", False):
            import urllib.request
            import urllib.error
            import json
            import time

            # Rate Limiting
            time.sleep(0.5)

            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=json.dumps({"query": "test", "api_key": val}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status != 200:
                        raise ValueError("Tavily API Key validation failed.")
            except urllib.error.URLError as e:
                if hasattr(e, 'code') and e.code == 401:
                    raise ValueError("Invalid Tavily API Key.")
                pass

        return v
=======
>>>>>>> REPLACE"""

with open("patch_config_tavily.patch", "w") as f:
    f.write(diff)
