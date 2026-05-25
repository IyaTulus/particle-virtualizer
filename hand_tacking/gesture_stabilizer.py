from collections import Counter, deque


class GestureStabilizer:
    def __init__(
        self, window_size: int = 7, min_votes: int = 5, initial: str = "UNKNOWN"
    ) -> None:
        self.window_size = window_size
        self.min_votes = min_votes
        self.history = deque(maxlen=window_size)
        self.last_stable = initial

    def update(self, gesture: str) -> str:
        self.history.append(gesture)

        if len(self.history) < self.window_size:
            return self.last_stable

        most_common_gesture, votes = Counter(self.history).most_common(1)[0]
        if votes >= self.min_votes:
            self.last_stable = most_common_gesture

        return self.last_stable
