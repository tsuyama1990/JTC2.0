import logging

from src.core.security import SecretMaskerFilter

# Apply global logging filter to mask secrets in all modules
logging.getLogger().addFilter(SecretMaskerFilter())
