"""
BAML Client Stub - Throws errors to trigger fallback analysis
"""

class BAMLClientStub:
    """Stub client that always throws to trigger fallback"""

    async def AnalyzeEssentialsDepth(self, **kwargs):
        """Stub method - raises to trigger fallback"""
        raise NotImplementedError("BAML Python client not generated - using fallback analysis")

    async def AnalyzePremiumDepth(self, **kwargs):
        """Stub method - raises to trigger fallback"""
        raise NotImplementedError("BAML Python client not generated - using fallback analysis")

# Export as 'b' to match expected import
b = BAMLClientStub()
