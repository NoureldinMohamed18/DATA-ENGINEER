# هذا الملف يقرأ الإعدادات من فولدر config
from pathlib import Path
import yaml

# __file__ = مسار هذا الملف نفسه (src/config.py)
# parents[0] = فولدر src
# parents[1] = فولدر المشروع كله
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_settings():
    # نفتح ملف الإعدادات بترميز يدعم العربي
    path = PROJECT_ROOT / "config" / "settings.yaml"
    with path.open(encoding="utf-8") as handle:
        # safe_load يحول النص إلى قاموس بايثون من غير تنفيذ كود
        return yaml.safe_load(handle)


def resolve_path(relative: str) -> Path:
    # مثال: "data/raw" يصبح مساراً كاملاً تحت المشروع
    return PROJECT_ROOT / relative
