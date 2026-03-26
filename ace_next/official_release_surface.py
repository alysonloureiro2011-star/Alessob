from .official_instagram_publish import OfficialInstagramPublishService
from .official_runtime_surface import OfficialRuntimeSurface


class OfficialReleaseSurface:
    def __init__(self, config):
        self.runtime = OfficialRuntimeSurface(config)
        self.instagram = OfficialInstagramPublishService(config)

    def snapshot(self):
        data = self.runtime.snapshot()
        data["instagram"] = self.instagram.readiness()
        data["release_surface"] = True
        return data
