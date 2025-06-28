"""
Lighting Runner Instance Management.

This module provides the global runner instance management to avoid circular imports.
"""
from typing import Optional
from shared.utils.logger import get_logger
from lighting.runner.base_runner import LightingBehaviorRunner
from lighting.services.behavior_manager import LightingBehaviorManager

logger = get_logger(__name__)

# Global runner instance (singleton)
_runner_instance: Optional[LightingBehaviorRunner] = None


def get_runner() -> LightingBehaviorRunner:
    """
    Get the global lighting runner instance.
    
    Returns:
        LightingBehaviorRunner instance
    """
    global _runner_instance
    if _runner_instance is None:
        # Create behavior manager
        behavior_manager = LightingBehaviorManager()
        # Create runner with real HAL (no mocks)
        _runner_instance = LightingBehaviorRunner(behavior_manager)
        logger.info("Lighting runner initialized with real HAL layer")
    return _runner_instance 