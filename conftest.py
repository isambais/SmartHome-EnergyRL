"""pytest kök conftest — proje kökünü sys.path'e ekler."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
