"""
Network intelligence package — persistent graph for multi-hop connection discovery,
people deduplication, connection strength scoring, and post-screening analysis.
"""
from .name_normalizer import NameNormalizer
from .graph_builder import NetworkGraphBuilder
from .path_finder import PathFinder, NetworkPath, FunderConnection, WarmPath
from .people_etl import PeopleETL
from .person_deduplication import PersonDeduplicationService
from .connection_strength import ConnectionStrengthScorer
from .batch_preprocessor import NetworkBatchPreprocessor
from .grant_wins import GrantWinService
from .post_screening_analyzer import PostScreeningAnalyzer, PostScreeningReport

__all__ = [
    "NameNormalizer",
    "NetworkGraphBuilder",
    "PathFinder",
    "NetworkPath",
    "FunderConnection",
    "WarmPath",
    "PeopleETL",
    "PersonDeduplicationService",
    "ConnectionStrengthScorer",
    "NetworkBatchPreprocessor",
    "GrantWinService",
    "PostScreeningAnalyzer",
    "PostScreeningReport",
]
