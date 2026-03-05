#!/usr/bin/env python3
"""
Grant Archetype Clustering - Semantic clustering of foundation giving patterns

Analyzes Schedule I grant purpose text across all foundations to create
~30 giving archetypes. Each foundation is then assigned its best-fit
archetype(s), enabling instant profile-to-foundation matching by mission area.

Two modes:
  1. Rule-based clustering (FREE, uses keyword patterns)
  2. AI-enhanced clustering (optional, uses Claude for semantic grouping)

Cost: $0 for rule-based, ~$2 for AI-enhanced (one-time)
Frequency: Quarterly or when new Schedule I data is loaded
"""

import json
import logging
import re
import sqlite3
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# PREDEFINED ARCHETYPE DEFINITIONS
# =============================================================================

# 30 grant-giving archetypes with keyword patterns and related NTEE codes
ARCHETYPE_DEFINITIONS = {
    "education_k12": {
        "label": "K-12 Education",
        "description": "Elementary and secondary education programs, school funding, teacher support",
        "keywords": ["school", "k-12", "elementary", "secondary", "student", "teacher",
                     "classroom", "literacy", "reading", "math", "stem education",
                     "after school", "afterschool", "tutoring", "charter school"],
        "ntee_codes": ["B20", "B21", "B24", "B25", "B28", "B29"],
    },
    "education_higher": {
        "label": "Higher Education",
        "description": "Colleges, universities, scholarships, academic research",
        "keywords": ["university", "college", "scholarship", "fellowship", "academic",
                     "tuition", "higher education", "campus", "undergraduate",
                     "graduate", "doctoral", "postdoctoral", "professorship"],
        "ntee_codes": ["B40", "B41", "B42", "B43", "B50"],
    },
    "education_workforce": {
        "label": "Workforce Development & Training",
        "description": "Job training, vocational education, career development",
        "keywords": ["workforce", "job training", "vocational", "career",
                     "employment", "skills training", "apprentice",
                     "professional development", "certification"],
        "ntee_codes": ["B60", "B70", "J20", "J21", "J22"],
    },
    "health_clinical": {
        "label": "Clinical Healthcare Services",
        "description": "Hospitals, clinics, patient care, medical services",
        "keywords": ["hospital", "clinic", "patient", "medical", "healthcare",
                     "health care", "treatment", "nursing", "primary care",
                     "emergency", "surgical", "diagnostic"],
        "ntee_codes": ["E20", "E21", "E22", "E30", "E31", "E32"],
    },
    "health_mental": {
        "label": "Mental Health & Behavioral",
        "description": "Mental health services, counseling, substance abuse treatment",
        "keywords": ["mental health", "counseling", "therapy", "behavioral",
                     "substance abuse", "addiction", "recovery", "psychiatric",
                     "suicide prevention", "crisis", "trauma"],
        "ntee_codes": ["F20", "F21", "F22", "F30", "F31", "F32", "F33"],
    },
    "health_research": {
        "label": "Medical Research",
        "description": "Biomedical research, clinical trials, disease research",
        "keywords": ["research", "biomedical", "clinical trial", "cancer research",
                     "medical research", "pharmaceutical", "genomic",
                     "disease", "cure", "laboratory"],
        "ntee_codes": ["H01", "H02", "H03", "H20", "H25", "H30"],
    },
    "health_public": {
        "label": "Public Health & Prevention",
        "description": "Public health programs, disease prevention, health education",
        "keywords": ["public health", "prevention", "vaccination", "immunization",
                     "health education", "wellness", "nutrition education",
                     "epidemiolog", "community health", "health screening"],
        "ntee_codes": ["E40", "E42", "E50", "E60", "E70", "E80"],
    },
    "human_services_basic": {
        "label": "Basic Needs & Emergency Services",
        "description": "Food banks, shelters, emergency assistance, clothing",
        "keywords": ["food bank", "food pantry", "shelter", "homeless",
                     "emergency assistance", "clothing", "meals", "hunger",
                     "soup kitchen", "basic needs", "emergency relief"],
        "ntee_codes": ["K30", "K31", "K34", "K35", "K36", "L41"],
    },
    "human_services_family": {
        "label": "Family & Children Services",
        "description": "Family support, child welfare, foster care, adoption",
        "keywords": ["family", "child welfare", "foster care", "adoption",
                     "parenting", "child abuse", "domestic violence",
                     "family counseling", "child care", "daycare", "early childhood"],
        "ntee_codes": ["P30", "P31", "P32", "P33", "P40", "P42"],
    },
    "human_services_youth": {
        "label": "Youth Development",
        "description": "Youth programs, mentoring, youth leadership, boys & girls clubs",
        "keywords": ["youth", "teen", "adolescent", "young people", "mentor",
                     "boys and girls club", "scouting", "4-h", "big brothers",
                     "youth development", "youth leadership", "youth empowerment"],
        "ntee_codes": ["O20", "O21", "O22", "O23", "O30", "O31"],
    },
    "human_services_elderly": {
        "label": "Aging & Senior Services",
        "description": "Senior services, aging programs, elder care, retirement",
        "keywords": ["senior", "elderly", "aging", "older adult", "retirement",
                     "nursing home", "assisted living", "meals on wheels",
                     "alzheimer", "dementia", "geriatric"],
        "ntee_codes": ["P50", "P51", "P52", "P54", "P58"],
    },
    "housing_community": {
        "label": "Housing & Community Development",
        "description": "Affordable housing, community development, neighborhood revitalization",
        "keywords": ["housing", "affordable housing", "community development",
                     "neighborhood", "revitalization", "urban development",
                     "rural development", "habitat for humanity", "homeownership"],
        "ntee_codes": ["L20", "L21", "L22", "L25", "L30", "S20", "S21"],
    },
    "arts_culture": {
        "label": "Arts & Culture",
        "description": "Museums, performing arts, visual arts, cultural programs",
        "keywords": ["museum", "art", "gallery", "theater", "theatre", "music",
                     "dance", "opera", "symphony", "orchestra", "cultural",
                     "performing arts", "visual arts", "film", "photography"],
        "ntee_codes": ["A20", "A23", "A25", "A26", "A30", "A40", "A50", "A51"],
    },
    "arts_humanities": {
        "label": "Humanities & History",
        "description": "History, literature, historic preservation, libraries",
        "keywords": ["history", "historic", "preservation", "library", "literary",
                     "humanities", "archaeology", "archive", "heritage",
                     "historical society", "restoration"],
        "ntee_codes": ["A60", "A70", "A80", "A84", "B70"],
    },
    "environment_conservation": {
        "label": "Environmental Conservation",
        "description": "Land conservation, wildlife protection, biodiversity",
        "keywords": ["conservation", "wildlife", "habitat", "biodiversity",
                     "endangered species", "land trust", "nature preserve",
                     "wetland", "forest", "marine", "ecosystem"],
        "ntee_codes": ["C30", "C32", "C34", "C35", "C36", "D30", "D31"],
    },
    "environment_climate": {
        "label": "Climate & Sustainability",
        "description": "Climate change, renewable energy, sustainability programs",
        "keywords": ["climate", "renewable energy", "solar", "wind energy",
                     "sustainability", "carbon", "greenhouse", "clean energy",
                     "environmental justice", "green", "recycling"],
        "ntee_codes": ["C01", "C20", "C27", "C60"],
    },
    "animal_welfare": {
        "label": "Animal Welfare",
        "description": "Animal shelters, veterinary care, animal rights",
        "keywords": ["animal", "pet", "veterinary", "spay", "neuter",
                     "animal shelter", "humane society", "rescue",
                     "animal welfare", "animal cruelty"],
        "ntee_codes": ["D20", "D30", "D31", "D32", "D33", "D34"],
    },
    "religion_faith": {
        "label": "Religious & Faith-Based",
        "description": "Churches, religious organizations, faith-based programs",
        "keywords": ["church", "religious", "faith", "ministry", "congregation",
                     "catholic", "christian", "jewish", "islamic", "buddhist",
                     "seminary", "missionary", "worship", "parish", "diocese"],
        "ntee_codes": ["X20", "X21", "X22", "X30", "X40", "X50"],
    },
    "international_development": {
        "label": "International Development",
        "description": "Global development, foreign aid, international programs",
        "keywords": ["international", "global", "foreign", "developing countries",
                     "africa", "asia", "latin america", "third world",
                     "humanitarian", "refugees", "migration", "peace"],
        "ntee_codes": ["Q20", "Q21", "Q22", "Q23", "Q30", "Q33"],
    },
    "civic_engagement": {
        "label": "Civic Engagement & Governance",
        "description": "Civic participation, voting, government accountability",
        "keywords": ["civic", "democracy", "voting", "election", "government",
                     "policy", "advocacy", "grassroots", "community organizing",
                     "public policy", "citizen", "nonprofit capacity"],
        "ntee_codes": ["R20", "R22", "R25", "R26", "R30", "W20"],
    },
    "legal_justice": {
        "label": "Legal Services & Justice",
        "description": "Legal aid, criminal justice reform, civil rights",
        "keywords": ["legal", "justice", "civil rights", "court", "law",
                     "prison", "incarceration", "reentry", "criminal justice",
                     "legal aid", "immigration legal", "discrimination"],
        "ntee_codes": ["I20", "I21", "I23", "I30", "I31", "I40", "R20"],
    },
    "disability_services": {
        "label": "Disability Services",
        "description": "Services for people with disabilities, accessibility, special needs",
        "keywords": ["disability", "disabled", "special needs", "accessibility",
                     "wheelchair", "deaf", "blind", "autism", "down syndrome",
                     "developmental disability", "adaptive", "inclusive"],
        "ntee_codes": ["P80", "P81", "P82", "P83", "P84", "P85", "P86"],
    },
    "veterans_military": {
        "label": "Veterans & Military Families",
        "description": "Veteran services, military family support, veteran healthcare",
        "keywords": ["veteran", "military", "armed forces", "service member",
                     "ptsd", "va ", "wounded warrior", "deployment",
                     "military family", "military spouse"],
        "ntee_codes": ["W30", "W60", "W70"],
    },
    "community_foundation": {
        "label": "Community Foundation & Philanthropy",
        "description": "Community foundations, donor-advised funds, philanthropic infrastructure",
        "keywords": ["community foundation", "donor advised", "endowment",
                     "philanthropy", "charitable giving", "grantmaking",
                     "fund development", "capacity building"],
        "ntee_codes": ["T20", "T21", "T22", "T30", "T31"],
    },
    "science_technology": {
        "label": "Science & Technology",
        "description": "STEM programs, scientific research, technology education",
        "keywords": ["science", "technology", "engineering", "stem",
                     "computer", "coding", "robotics", "space",
                     "astronomy", "physics", "chemistry", "biology"],
        "ntee_codes": ["U20", "U21", "U30", "U33", "U40", "U50"],
    },
    "recreation_sports": {
        "label": "Recreation & Sports",
        "description": "Athletic programs, parks, recreation facilities, sports leagues",
        "keywords": ["recreation", "sport", "athletic", "park", "playground",
                     "swimming", "baseball", "basketball", "soccer", "football",
                     "fitness", "outdoor", "camping", "trail"],
        "ntee_codes": ["N20", "N30", "N31", "N32", "N40", "N50", "N60"],
    },
    "economic_development": {
        "label": "Economic & Small Business Development",
        "description": "Small business support, microfinance, economic empowerment",
        "keywords": ["economic development", "small business", "microfinance",
                     "entrepreneurship", "microloan", "business incubator",
                     "economic empowerment", "financial literacy",
                     "economic opportunity"],
        "ntee_codes": ["S30", "S31", "S40", "S41", "S43", "S46", "S47"],
    },
    "racial_equity": {
        "label": "Racial Equity & Social Justice",
        "description": "Racial justice, equity initiatives, diversity programs",
        "keywords": ["racial equity", "social justice", "diversity", "inclusion",
                     "equity", "anti-racism", "civil rights", "black",
                     "latino", "indigenous", "native american", "asian",
                     "racial justice", "equal opportunity"],
        "ntee_codes": ["R20", "R22", "R25"],
    },
    "media_journalism": {
        "label": "Media & Journalism",
        "description": "Independent journalism, press freedom, media literacy",
        "keywords": ["journalism", "media", "press", "news", "broadcast",
                     "documentary", "reporting", "media literacy",
                     "public broadcasting", "editorial"],
        "ntee_codes": ["A33", "A34"],
    },
    "general_operating": {
        "label": "General Operating & Unrestricted",
        "description": "General operating support, unrestricted funding, capacity building",
        "keywords": ["general operating", "unrestricted", "general support",
                     "operating support", "core support", "general purpose",
                     "annual fund", "general operations"],
        "ntee_codes": [],  # Can apply to any NTEE code
    },
}


@dataclass
class ArchetypeAssignment:
    """Archetype assignment for a single foundation."""
    ein: str
    primary_archetype: str
    primary_confidence: float
    secondary_archetypes: List[str] = field(default_factory=list)
    matching_keywords_found: List[str] = field(default_factory=list)


@dataclass
class ClusteringStats:
    """Statistics from archetype clustering run."""
    foundations_analyzed: int = 0
    foundations_assigned: int = 0
    archetype_distribution: Dict[str, int] = field(default_factory=dict)
    unclassified_count: int = 0
    execution_time_ms: float = 0.0


class GrantArchetypeClustering:
    """
    Assigns giving archetypes to foundations based on Schedule I grant purposes.

    Uses rule-based keyword matching against predefined archetype definitions.
    Can optionally use AI for ambiguous cases.
    """

    def __init__(self, intelligence_db_path: str):
        self.intelligence_db_path = intelligence_db_path
        self.archetypes = ARCHETYPE_DEFINITIONS

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.intelligence_db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def run_clustering(self) -> ClusteringStats:
        """
        Run archetype clustering on all foundations.

        Sources:
          1. Schedule I grant purposes (from schedule_i_grant_analyzer data)
          2. NTEE codes (from BMF)
          3. Foundation narratives (if extracted)

        Updates: foundation_intelligence_index with archetype assignments
        """
        start_time = time.time()
        stats = ClusteringStats()
        conn = self._get_connection()

        try:
            # Ensure grant_archetypes reference table is populated
            self._populate_archetype_reference(conn)

            # Get all foundations with their available data
            foundations = self._load_foundation_signals(conn)
            stats.foundations_analyzed = len(foundations)

            # Assign archetypes
            assignments = []
            for ein, signals in foundations.items():
                assignment = self._assign_archetype(ein, signals)
                if assignment:
                    assignments.append(assignment)
                    stats.archetype_distribution[assignment.primary_archetype] = (
                        stats.archetype_distribution.get(assignment.primary_archetype, 0) + 1
                    )
                    stats.foundations_assigned += 1
                else:
                    stats.unclassified_count += 1

            # Write assignments to foundation_intelligence_index
            self._write_archetype_assignments(conn, assignments)

            # Update archetype reference table with counts
            self._update_archetype_counts(conn)

            conn.commit()
            stats.execution_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Clustering complete: {stats.foundations_assigned}/{stats.foundations_analyzed} "
                f"assigned, {stats.unclassified_count} unclassified"
            )

            return stats

        finally:
            conn.close()

    def _load_foundation_signals(self, conn: sqlite3.Connection) -> Dict[str, Dict]:
        """
        Load all available signals for archetype assignment.
        Combines NTEE codes, grant purposes, and narrative data.
        """
        foundations: Dict[str, Dict] = {}

        # 1. Get NTEE codes from BMF
        try:
            cursor = conn.execute("""
                SELECT ein, ntee_code
                FROM bmf_organizations
                WHERE foundation_code IS NOT NULL
                  AND ntee_code IS NOT NULL
            """)
            for row in cursor:
                ein = row["ein"]
                if ein not in foundations:
                    foundations[ein] = {"ntee_codes": [], "grant_purposes": [], "narratives": []}
                foundations[ein]["ntee_codes"].append(row["ntee_code"])
        except sqlite3.OperationalError:
            logger.warning("Could not load NTEE codes from bmf_organizations")

        # 2. Get foundation narratives if available
        try:
            cursor = conn.execute("""
                SELECT ein, mission_statement, stated_priorities, program_descriptions
                FROM foundation_narratives
                WHERE mission_statement IS NOT NULL
            """)
            for row in cursor:
                ein = row["ein"]
                if ein not in foundations:
                    foundations[ein] = {"ntee_codes": [], "grant_purposes": [], "narratives": []}
                if row["mission_statement"]:
                    foundations[ein]["narratives"].append(row["mission_statement"])
                if row["stated_priorities"]:
                    try:
                        priorities = json.loads(row["stated_priorities"])
                        foundations[ein]["narratives"].extend(priorities)
                    except json.JSONDecodeError:
                        pass
        except sqlite3.OperationalError:
            logger.info("foundation_narratives table not available")

        # 3. Get grant purposes from web intelligence or Schedule I data
        # (This would integrate with schedule_i_grant_analyzer_tool output)
        try:
            cursor = conn.execute("""
                SELECT ein, program_data
                FROM web_intelligence
                WHERE program_data IS NOT NULL
            """)
            for row in cursor:
                ein = row["ein"]
                if ein not in foundations:
                    foundations[ein] = {"ntee_codes": [], "grant_purposes": [], "narratives": []}
                try:
                    programs = json.loads(row["program_data"])
                    for prog in programs:
                        if isinstance(prog, dict):
                            desc = prog.get("description", "")
                            if desc:
                                foundations[ein]["grant_purposes"].append(desc)
                        elif isinstance(prog, str):
                            foundations[ein]["grant_purposes"].append(prog)
                except json.JSONDecodeError:
                    pass
        except sqlite3.OperationalError:
            logger.info("web_intelligence table not available for grant purposes")

        # Also include foundations that only have intelligence index data
        try:
            cursor = conn.execute("""
                SELECT ein, ntee_code
                FROM foundation_intelligence_index
                WHERE ein NOT IN (SELECT ein FROM bmf_organizations WHERE ntee_code IS NOT NULL)
                  AND ntee_code IS NOT NULL
            """)
            for row in cursor:
                ein = row["ein"]
                if ein not in foundations:
                    foundations[ein] = {"ntee_codes": [], "grant_purposes": [], "narratives": []}
                    foundations[ein]["ntee_codes"].append(row["ntee_code"])
        except sqlite3.OperationalError:
            pass

        return foundations

    def _assign_archetype(self, ein: str, signals: Dict) -> Optional[ArchetypeAssignment]:
        """
        Assign archetype(s) to a foundation based on available signals.

        Priority:
          1. Grant purpose text keyword matching (strongest signal)
          2. Narrative/mission keyword matching
          3. NTEE code mapping
        """
        archetype_scores: Dict[str, float] = defaultdict(float)
        keywords_found: Dict[str, List[str]] = defaultdict(list)

        # Combine all text signals
        all_text = " ".join(signals.get("grant_purposes", []) + signals.get("narratives", []))
        all_text_lower = all_text.lower()

        # Score each archetype
        for arch_id, arch_def in self.archetypes.items():
            score = 0.0

            # 1. Keyword matching in text (weight: 3.0 per match)
            if all_text_lower:
                for keyword in arch_def["keywords"]:
                    if keyword.lower() in all_text_lower:
                        score += 3.0
                        keywords_found[arch_id].append(keyword)

            # 2. NTEE code matching (weight: 5.0 per match)
            for ntee in signals.get("ntee_codes", []):
                if ntee in arch_def.get("ntee_codes", []):
                    score += 5.0
                # Major group match (first letter)
                elif ntee and arch_def.get("ntee_codes") and any(
                    ntee[0] == nc[0] for nc in arch_def["ntee_codes"] if nc
                ):
                    score += 2.0

            if score > 0:
                archetype_scores[arch_id] = score

        if not archetype_scores:
            return None

        # Sort by score descending
        sorted_archetypes = sorted(archetype_scores.items(), key=lambda x: x[1], reverse=True)

        primary = sorted_archetypes[0]
        max_possible = max(
            len(arch_def["keywords"]) * 3.0 + len(arch_def.get("ntee_codes", [])) * 5.0
            for arch_def in self.archetypes.values()
        )
        confidence = min(1.0, primary[1] / max(1.0, max_possible * 0.3))

        # Secondary archetypes (score >= 50% of primary)
        threshold = primary[1] * 0.5
        secondaries = [aid for aid, score in sorted_archetypes[1:4] if score >= threshold]

        return ArchetypeAssignment(
            ein=ein,
            primary_archetype=primary[0],
            primary_confidence=round(confidence, 3),
            secondary_archetypes=secondaries,
            matching_keywords_found=keywords_found.get(primary[0], []),
        )

    def _write_archetype_assignments(
        self, conn: sqlite3.Connection, assignments: List[ArchetypeAssignment]
    ):
        """Write archetype assignments to foundation_intelligence_index."""
        for assignment in assignments:
            try:
                conn.execute("""
                    UPDATE foundation_intelligence_index
                    SET primary_archetype = ?,
                        secondary_archetypes = ?,
                        archetype_confidence = ?
                    WHERE ein = ?
                """, (
                    assignment.primary_archetype,
                    json.dumps(assignment.secondary_archetypes),
                    assignment.primary_confidence,
                    assignment.ein,
                ))
            except sqlite3.OperationalError:
                pass

    def _populate_archetype_reference(self, conn: sqlite3.Connection):
        """Populate the grant_archetypes reference table."""
        for arch_id, arch_def in self.archetypes.items():
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO grant_archetypes (
                        archetype_id, archetype_label, archetype_description,
                        example_purposes, related_ntee_codes, keyword_patterns,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    arch_id,
                    arch_def["label"],
                    arch_def["description"],
                    json.dumps([]),  # Example purposes populated from actual data
                    json.dumps(arch_def.get("ntee_codes", [])),
                    json.dumps(arch_def["keywords"]),
                    datetime.now().isoformat(),
                ))
            except sqlite3.OperationalError:
                pass

    def _update_archetype_counts(self, conn: sqlite3.Connection):
        """Update foundation_count and total_grant_volume in grant_archetypes."""
        try:
            cursor = conn.execute("""
                SELECT primary_archetype, COUNT(*) as cnt, SUM(grants_paid_latest) as total_grants
                FROM foundation_intelligence_index
                WHERE primary_archetype IS NOT NULL
                GROUP BY primary_archetype
            """)
            for row in cursor:
                conn.execute("""
                    UPDATE grant_archetypes
                    SET foundation_count = ?, total_grant_volume = ?
                    WHERE archetype_id = ?
                """, (row["cnt"], row["total_grants"] or 0, row["primary_archetype"]))
        except sqlite3.OperationalError:
            pass

    def get_archetypes_for_profile(
        self, focus_areas: List[str], ntee_codes: List[str], mission: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Find matching archetypes for a profile's focus areas.
        Returns: [(archetype_id, confidence_score), ...]
        """
        all_text = " ".join(focus_areas)
        if mission:
            all_text += " " + mission
        all_text_lower = all_text.lower()

        scores: Dict[str, float] = {}
        for arch_id, arch_def in self.archetypes.items():
            score = 0.0

            # Keyword matches
            for keyword in arch_def["keywords"]:
                if keyword.lower() in all_text_lower:
                    score += 3.0

            # NTEE matches
            for ntee in ntee_codes:
                if ntee in arch_def.get("ntee_codes", []):
                    score += 5.0
                elif ntee and arch_def.get("ntee_codes") and any(
                    ntee[0] == nc[0] for nc in arch_def["ntee_codes"] if nc
                ):
                    score += 2.0

            if score > 0:
                # Normalize to 0-1 range
                max_score = len(arch_def["keywords"]) * 3.0 + len(arch_def.get("ntee_codes", [])) * 5.0
                scores[arch_id] = min(1.0, score / max(1.0, max_score * 0.3))

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
