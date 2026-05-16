"""Compatibility wrapper for the active detector implementation.

Older scripts imported ``pipeline.detector_fixed`` while the maintained
implementation now lives in ``pipeline.detector``.
"""

from pipeline.detector import *  # noqa: F401,F403
