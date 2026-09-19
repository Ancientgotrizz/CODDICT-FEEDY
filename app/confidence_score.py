"""
confidence_score.py
--------------------
Combines three separate confidence signals into one final trust number:
  1. llm_confidence      - how sure the AI model itself claims to be
  2. neighbour_agreement - how many of the retrieved labelled examples
                            agree with the model's chosen category
  3. extraction_quality  - how reliable the extracted text appears to be
                            (lower when OCR had to be used)

This produces a confidence ESTIMATE, not a statistically calibrated
probability. All inputs are clamped to the range [0, 1] first.
"""


def fuse_confidence(llm_confidence, neighbour_agreement, extraction_quality=1.0):
    """Blends the three signals above into one rounded confidence score."""
    llm_confidence = max(0.0, min(1.0, llm_confidence))
    neighbour_agreement = max(0.0, min(1.0, neighbour_agreement))
    extraction_quality = max(0.0, min(1.0, extraction_quality))

    base_confidence = (
      (0.50 * llm_confidence)
      + (0.30 * neighbour_agreement)
      + (0.20 * extraction_quality)
    )

    return round(base_confidence, 2)
