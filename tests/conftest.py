import sys
from pathlib import Path

# Add project root and src to python path for tests
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))
