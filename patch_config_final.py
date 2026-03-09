
with open("src/core/config.py") as f:
    content = f.read()

diff = """<<<<<<< SEARCH
    max_query_length: int = Field(
        default=DEFAULT_RAG_MAX_QUERY_LENGTH,
        description="Max query length",
    )
    max_recursion_depth: int = Field(
        default=DEFAULT_MAX_RECURSION,
        description="Max recursion depth for directory scanning",
    )
    batch_size: int = Field(
        default=DEFAULT_RAG_BATCH_SIZE,
        description="Batch size for RAG ingestion",
    )
    max_files: int = Field(
        default=DEFAULT_MAX_FILES,
        description="Maximum number of files to process",
    )
=======
    max_query_length: int = Field(
        default=DEFAULT_RAG_MAX_QUERY_LENGTH,
        description="Max query length",
    )
    max_recursion_depth: int = Field(
        default=DEFAULT_MAX_RECURSION,
        description="Max recursion depth for directory scanning",
    )
    max_files: int = Field(
        default=DEFAULT_MAX_FILES,
        description="Maximum number of files to process",
    )
>>>>>>> REPLACE"""

with open("patch_config_final.patch", "w") as f:
    f.write(diff)
