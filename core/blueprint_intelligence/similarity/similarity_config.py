"""BI-4 Similarity Configuration."""

from dataclasses import dataclass

@dataclass(slots=True)
class SimilarityConfig:
    """Deterministic similarity scoring weights."""

    type_weight: float = 0.30
    region_weight: float = 0.20
    pattern_weight: float = 0.25
    dimension_weight: float = 0.15
    source_weight: float = 0.10

    def __post_init__(self) -> None:
        """Validate weights."""
        weights = [
            self.type_weight,
            self.region_weight,
            self.pattern_weight,
            self.dimension_weight,
            self.source_weight,
        ]

        for weight in weights:
            if not isinstance(weight, (int, float)) or isinstance(weight, bool):
                raise TypeError("All weights must be numbers")
            if not 0.0 <= weight <= 1.0:
                raise ValueError("All weights must be between 0.0 and 1.0")

        total = sum(weights)
        if total <= 0:
            raise ValueError("Sum of weights must be greater than 0")

    def normalized_weights(self) -> tuple[float, float, float, float, float]:
        """Return weights normalized to sum to 1.0."""
        total = (
            self.type_weight
            + self.region_weight
            + self.pattern_weight
            + self.dimension_weight
            + self.source_weight
        )

        if total == 0:
            return (0.0, 0.0, 0.0, 0.0, 0.0)

        norm_type = self.type_weight / total
        norm_region = self.region_weight / total
        norm_pattern = self.pattern_weight / total
        norm_dimension = self.dimension_weight / total
        norm_source = self.source_weight / total

        return (norm_type, norm_region, norm_pattern, norm_dimension, norm_source)

__all__ = ["SimilarityConfig"]
