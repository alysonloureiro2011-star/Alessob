from .official_runtime import OfficialRuntime
from .official_instagram_publish import OfficialInstagramPublishService


class OfficialReleaseSurface:
    def __init__(self, config):
        self.runtime = OfficialRuntime(config)
        self.instagram = OfficialInstagramPublishService(config)

    def snapshot(self):
        data = self.runtime.snapshot()
        data["instagram"] = self.instagram.readiness()
        data["release_surface"] = True
        return data
