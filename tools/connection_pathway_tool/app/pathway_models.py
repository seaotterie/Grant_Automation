"""
Connection Pathway Tool Data Models
Multi-hop warm introduction pathway discovery between seeker and funder.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class PathwayStrength(Enum):
    DIRECT = "direct"           # 1 hop -- same person at both orgs
    STRONG = "strong"           # 2 hops -- one intermediary
    MODERATE = "moderate"       # 3 hops -- two intermediaries
    WEAK = "weak"               # 4 hops -- three intermediaries
    NONE = "none"               # no pathway found


@dataclass
class PathwayNode:
    person_name: str
    title: Optional[str]
    organization_name: str
    organization_ein: Optional[str]
    org_type: str               # seeker, intermediary, funder
    role_at_org: str            # board, executive, staff, advisory
    influence_score: float = 0.0


@dataclass
class IntroductionPathway:
    pathway_id: str
    degree: int                 # number of hops (1-4)
    strength: PathwayStrength
    aggregate_strength: float   # product of edge strengths along path (0-1)
    nodes: list                 # list of PathwayNode dicts
    connection_basis: str       # human-readable description of how connected
    cultivation_strategy: str = ""   # AI-generated strategy
    estimated_timeline: str = ""     # "2-4 weeks", "1-3 months", etc.
    success_probability: float = 0.0 # 0-1


@dataclass
class ConnectionPathwayInput:
    profile_id: str
    target_funder_ein: str
    target_funder_name: str = ""
    max_hops: int = 4
    include_cultivation_strategy: bool = True  # requires AI call if True
    seeker_org_name: str = ""
    seeker_board_members: list = field(default_factory=list)


@dataclass
class ConnectionPathwayOutput:
    profile_id: str
    target_funder_ein: str
    target_funder_name: str
    pathways: list              # list of IntroductionPathway
    best_pathway: Optional[dict] = None  # the strongest pathway
    network_proximity_score: float = 0.0  # 0-100 composite score
    total_pathways_found: int = 0
    coverage_summary: str = ""   # "2 direct connections, 5 two-hop pathways"
    recommendations: list = field(default_factory=list)  # strategic recommendations
