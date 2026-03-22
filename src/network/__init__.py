"""
Network intelligence package — persistent graph for multi-hop connection discovery,
people deduplication, and connection strength scoring.
"""
from .name_normalizer import NameNormalizer
from .graph_builder import NetworkGraphBuilder
from .path_finder import PathFinder, NetworkPath
from .people_etl import PeopleETL
from .person_deduplication import PersonDeduplicationService
from .connection_strength import ConnectionStrengthScorer

__all__ = [
    "NameNormalizer",
    "NetworkGraphBuilder",
    "PathFinder",
    "NetworkPath",
    "PeopleETL",
    "PersonDeduplicationService",
    "ConnectionStrengthScorer",
]
