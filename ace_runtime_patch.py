from ace_next.official_runtime_phase3 import OfficialRuntime
from ace_next.config import AceNextConfig

_runtime = None


def get_runtime():
    global _runtime
    if _runtime is None:
        config = AceNextConfig()
        _runtime = OfficialRuntime(config)
    return _runtime


def run_pipeline(trend: str, **kwargs):
    runtime = get_runtime()
    return runtime.run(trend=trend, **kwargs)
