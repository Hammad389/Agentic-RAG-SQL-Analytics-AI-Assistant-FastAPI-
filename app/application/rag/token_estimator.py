class TokenEstimator:
    """
    Lightweight token estimation.
    Approximation: 1 token ≈ 4 characters (English text average).
    """

    @staticmethod
    def estimate(text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)
