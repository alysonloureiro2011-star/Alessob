import time
from typing import Dict, List


class WorldModel:

    def __init__(self):

        self.trend_memory: List[Dict] = []
        self.max_memory = 200

        self.topic_frequency = {}

    # --------------------------------------------------

    def observe_trend(self, trend: str):

        record = {
            "trend": trend,
            "timestamp": time.time()
        }

        self.trend_memory.append(record)

        if len(self.trend_memory) > self.max_memory:
            self.trend_memory.pop(0)

        self.topic_frequency[trend] = self.topic_frequency.get(trend, 0) + 1

    # --------------------------------------------------

    def is_saturated(self, trend: str) -> bool:

        count = self.topic_frequency.get(trend, 0)

        if count > 5:
            return True

        return False

    # --------------------------------------------------

    def emerging_trends(self) -> List[str]:

        emerging = []

        for trend, count in self.topic_frequency.items():

            if count <= 2:
                emerging.append(trend)

        return emerging

    # --------------------------------------------------

    def dominant_trends(self) -> List[str]:

        dominant = []

        for trend, count in self.topic_frequency.items():

            if count >= 4:
                dominant.append(trend)

        return dominant

    # --------------------------------------------------

    def world_snapshot(self) -> Dict:

        return {
            "observed_trends": len(self.trend_memory),
            "unique_topics": len(self.topic_frequency),
            "dominant_trends": self.dominant_trends(),
            "emerging_trends": self.emerging_trends(),
        }


world_model = WorldModel()
