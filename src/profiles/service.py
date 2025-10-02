"""
DEPRECATED: ProfileService with file-based locking

This module is deprecated as of Phase 8 (2025-10-01).
Use UnifiedProfileService instead: src.profiles.unified_service

Legacy ProfileService archived at: src/profiles/_deprecated/service_legacy.py

Why deprecated:
- 100+ lines of file-based locking complexity (unnecessary for single-user app)
- Dual-layer locking (file + thread) adds overhead
- Flat file structure replaced by directory-based organization
- Separate sessions directory replaced by embedded sessions

Replaced by:
- UnifiedProfileService: Simpler architecture, no locking, embedded analytics
- 27% code reduction (687 → ~600 lines)
- Better performance (no locking overhead)
- Real-time embedded analytics

Migration guide: docs/12-factor-transformation/PROFILE_SERVICE_MIGRATION_PLAN.md
"""

import warnings
from src.profiles.unified_service import get_unified_profile_service

# Issue deprecation warning
warnings.warn(
    "ProfileService is deprecated and will be removed in Phase 9. "
    "Use UnifiedProfileService instead: from src.profiles.unified_service import get_unified_profile_service",
    DeprecationWarning,
    stacklevel=2
)


def get_profile_service():
    """
    DEPRECATED: Returns UnifiedProfileService for backward compatibility.

    This function is a compatibility shim. Update your code to use:
        from src.profiles.unified_service import get_unified_profile_service
        profile_service = get_unified_profile_service()
    """
    warnings.warn(
        "get_profile_service() is deprecated. Use get_unified_profile_service() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_unified_profile_service()


# For backward compatibility - redirect to UnifiedProfileService
ProfileService = type('ProfileService', (), {
    '__init__': lambda self: warnings.warn(
        "ProfileService class is deprecated. Use UnifiedProfileService instead.",
        DeprecationWarning,
        stacklevel=2
    ) or get_unified_profile_service().__init__(),
    '__getattr__': lambda self, name: getattr(get_unified_profile_service(), name)
})
