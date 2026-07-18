"""Errors raised by Blueprint Intelligence extractors."""


class BlueprintExtractionError(Exception):
    """Base error for failures while extracting Blueprint objects."""


class UnsupportedBlueprintSourceError(BlueprintExtractionError):
    """Raised when an extractor receives a source it does not support."""


class InvalidKnowledgeDatasetError(BlueprintExtractionError):
    """Raised when a Knowledge Dataset file cannot be decoded as valid JSON."""


class InvalidBlueprintJsonError(BlueprintExtractionError):
    """Raised when Blueprint JSON cannot be decoded into BI-1 Blueprint objects."""


class InvalidOTBMBlueprintError(BlueprintExtractionError):
    """Raised when OTBM-compatible data cannot be converted into a Blueprint."""
