#!/usr/bin/env python3
"""
Intelligent Classifier for Organizations Without NTEE Codes
Multi-dimensional analysis to identify promising grant candidates.
"""

import re
import asyncio
import logging
import sqlite3
from typing import Dict, List, Set, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import csv
from dataclasses import dataclass

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.utils.decorators import retry_on_failure


@dataclass
class ClassificationCriteria:
    """Configuration for classification criteria."""
    
    # Keyword categories with weights
    health_keywords: List[str]
    nutrition_keywords: List[str] 
    safety_keywords: List[str]
    education_keywords: List[str]
    
    # Financial thresholds
    min_assets: Optional[float] = 100000
    max_assets: Optional[float] = None
    min_revenue: Optional[float] = 50000
    max_revenue: Optional[float] = None
    
    # Geographic filters
    target_zip_prefixes: List[str] = None
    excluded_zip_prefixes: List[str] = None
    
    # Foundation type preferences
    preferred_foundation_codes: List[str] = None
    excluded_foundation_codes: List[str] = None
    
    # Activity code patterns
    activity_code_patterns: List[str] = None


class IntelligentClassifier(BaseProcessor):
    """
    Advanced classifier for organizations without NTEE codes.
    
    Uses multiple signals to identify potential grant candidates:
    - Organizational name keyword analysis
    - Financial health indicators
    - Geographic clustering
    - Foundation type analysis
    - Activity code patterns
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="intelligent_classifier",
            description="Classify organizations without NTEE codes using multiple indicators",
            version="1.0.0",
            dependencies=["bmf_filter"],
            estimated_duration=60,
            requires_network=False,
            requires_api_key=False,
            can_run_parallel=True,
            processor_type="analysis"
        )
        super().__init__(metadata)
        
        # Default classification criteria
        self.default_criteria = ClassificationCriteria(
            health_keywords=[
                'health', 'medical', 'clinic', 'hospital', 'wellness', 'mental health',
                'healthcare', 'community health', 'public health', 'behavioral health',
                'medicare', 'medicaid', 'patient', 'care', 'treatment', 'therapy',
                'rehabilitation', 'recovery', 'nursing', 'physician', 'doctor',
                'surgery', 'cancer', 'diabetes', 'heart', 'disease', 'prevention'
            ],
            nutrition_keywords=[
                'food', 'nutrition', 'hunger', 'meals', 'pantry', 'kitchen',
                'feeding', 'nourishment', 'diet', 'culinary', 'cooking',
                'grocery', 'fresh', 'organic', 'farm', 'agriculture',
                'supplements', 'vitamins', 'obesity', 'malnutrition'
            ],
            safety_keywords=[
                'safety', 'emergency', 'fire', 'rescue', 'disaster', 'prevention',
                'security', 'protection', 'crisis', 'response', 'first aid',
                'paramedic', 'ambulance', 'trauma', 'violence', 'abuse',
                'domestic violence', 'child protection', 'elder abuse'
            ],
            education_keywords=[
                'education', 'school', 'learning', 'training', 'scholarship',
                'literacy', 'academic', 'curriculum', 'teacher', 'student',
                'university', 'college', 'kindergarten', 'preschool'
            ],
            min_assets=100000,
            min_revenue=50000,
            target_zip_prefixes=['22', '23', '24'],  # Virginia ZIP prefixes
            activity_code_patterns=['0', '1', '2', '3']  # Common nonprofit activity codes
        )
    
    def _extract_keywords_from_name(self, name: str) -> Set[str]:
        """Extract meaningful keywords from organization name."""
        if not name:
            return set()
        
        # Clean and normalize
        cleaned = re.sub(r'[^\w\s]', ' ', name.lower())
        words = set(cleaned.split())
        
        # Remove common stop words
        stop_words = {
            'inc', 'llc', 'corp', 'corporation', 'company', 'foundation',
            'association', 'society', 'institute', 'center', 'centre',
            'group', 'organization', 'the', 'of', 'and', 'for', 'in'
        }
        
        return words - stop_words
    
    def _calculate_keyword_score(self, org_name: str, criteria: ClassificationCriteria) -> Dict[str, float]:
        """Calculate keyword matching scores for different categories."""
        keywords = self._extract_keywords_from_name(org_name)
        
        scores = {
            'health': 0.0,
            'nutrition': 0.0,
            'safety': 0.0,
            'education': 0.0
        }
        
        # Calculate category scores
        for keyword in keywords:
            if keyword in criteria.health_keywords:
                scores['health'] += 1.0
            if keyword in criteria.nutrition_keywords:
                scores['nutrition'] += 1.0
            if keyword in criteria.safety_keywords:
                scores['safety'] += 1.0
            if keyword in criteria.education_keywords:
                scores['education'] += 1.0
        
        # Normalize by number of keywords in name
        total_keywords = max(len(keywords), 1)
        return {k: v / total_keywords for k, v in scores.items()}
    
    def _calculate_financial_score(self, org_data: Dict[str, Any], criteria: ClassificationCriteria) -> float:
        """Calculate financial health score."""
        score = 0.0
        
        assets = org_data.get('assets')
        revenue = org_data.get('revenue')
        
        # Asset score (0-0.4)
        if assets:
            if criteria.min_assets and assets >= criteria.min_assets:
                score += 0.2
            if assets >= 500000:  # Substantial assets
                score += 0.2
        
        # Revenue score (0-0.4)
        if revenue:
            if criteria.min_revenue and revenue >= criteria.min_revenue:
                score += 0.2
            if revenue >= 250000:  # Meaningful revenue
                score += 0.2
        
        # Balance score (0-0.2)
        if assets and revenue and revenue > 0:
            ratio = assets / revenue
            if 1 <= ratio <= 10:  # Healthy asset-to-revenue ratio
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_geographic_score(self, org_data: Dict[str, Any], criteria: ClassificationCriteria) -> float:
        """Calculate geographic preference score."""
        if not criteria.target_zip_prefixes:
            return 0.5  # Neutral if no preference
        
        zip_code = org_data.get('zip', '')
        if not zip_code:
            return 0.0
        
        # Extract ZIP prefix
        zip_prefix = zip_code[:2] if len(zip_code) >= 2 else zip_code
        
        if zip_prefix in criteria.target_zip_prefixes:
            return 1.0
        
        return 0.0
    
    def _calculate_foundation_score(self, org_data: Dict[str, Any], criteria: ClassificationCriteria) -> float:
        """Calculate foundation type preference score."""
        foundation_code = org_data.get('foundation_code', '')
        
        if criteria.preferred_foundation_codes:
            if foundation_code in criteria.preferred_foundation_codes:
                return 1.0
        
        if criteria.excluded_foundation_codes:
            if foundation_code in criteria.excluded_foundation_codes:
                return 0.0
        
        # Default scoring based on common patterns
        if foundation_code in ['10', '15', '16']:  # Public charities
            return 0.8
        elif foundation_code in ['00', '03']:  # Private foundations
            return 0.6
        
        return 0.5  # Neutral
    
    def _calculate_activity_score(self, org_data: Dict[str, Any], criteria: ClassificationCriteria) -> float:
        """Calculate activity code relevance score."""
        activity_code = org_data.get('activity_code', '')
        
        if not activity_code or not criteria.activity_code_patterns:
            return 0.5
        
        # Check if activity code matches patterns
        for pattern in criteria.activity_code_patterns:
            if activity_code.startswith(pattern):
                return 1.0
        
        return 0.3
    
    def _analyze_qualification_factors(self, keyword_scores: Dict[str, float], financial_score: float, 
                                     geographic_score: float, foundation_score: float, activity_score: float,
                                     weights: Dict[str, float], org_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze what factors make this organization qualify and determine primary reason."""
        
        # Calculate weighted contributions
        best_keyword_score = max(keyword_scores.values())
        weighted_contributions = {
            'keyword_match': weights['keyword'] * best_keyword_score,
            'financial_strength': weights['financial'] * financial_score,
            'geographic_match': weights['geographic'] * geographic_score,
            'foundation_type': weights['foundation'] * foundation_score,
            'activity_pattern': weights['activity'] * activity_score
        }
        
        # Find primary qualifying factor
        primary_factor = max(weighted_contributions, key=weighted_contributions.get)
        primary_contribution = weighted_contributions[primary_factor]
        
        # Determine qualification strength
        total_score = sum(weighted_contributions.values())
        if total_score >= 0.7:
            strength = "Strong"
        elif total_score >= 0.5:
            strength = "Good"
        elif total_score >= 0.3:
            strength = "Moderate"
        else:
            strength = "Weak"
        
        # Create detailed qualification analysis
        qualification_details = []
        
        # Keyword analysis
        if best_keyword_score > 0.1:
            best_category = max(keyword_scores, key=keyword_scores.get)
            qualification_details.append(f"Keywords: {best_category} match ({best_keyword_score:.2f})")
        
        # Financial analysis
        if financial_score > 0.3:
            assets = org_data.get('assets', 0)
            revenue = org_data.get('revenue', 0)
            financial_details = []
            if assets and assets >= 100000:
                financial_details.append(f"${assets:,.0f} assets")
            if revenue and revenue >= 50000:
                financial_details.append(f"${revenue:,.0f} revenue")
            if financial_details:
                qualification_details.append(f"Financial: {', '.join(financial_details)}")
        
        # Foundation type analysis
        if foundation_score > 0.6:
            foundation_code = org_data.get('foundation_code', '')
            foundation_types = {
                '10': 'Public Charity (501c3)',
                '15': 'Public Charity (509a1)',
                '16': 'Public Charity (509a2)', 
                '00': 'Private Foundation',
                '03': 'Private Operating Foundation'
            }
            foundation_type = foundation_types.get(foundation_code, f"Foundation Code {foundation_code}")
            qualification_details.append(f"Foundation: {foundation_type}")
        
        # Geographic analysis
        if geographic_score > 0.5:
            city = org_data.get('city', '')
            state = org_data.get('state', '')
            qualification_details.append(f"Location: {city}, {state}")
        
        # Create human-readable primary reason
        reason_mapping = {
            'keyword_match': f"Strong keyword match ({max(keyword_scores, key=keyword_scores.get)})",
            'financial_strength': f"Financial capacity (Score: {financial_score:.2f})",
            'geographic_match': f"Geographic targeting ({org_data.get('city', '')}, {org_data.get('state', '')})",
            'foundation_type': f"Preferred foundation type ({org_data.get('foundation_code', '')})",
            'activity_pattern': f"Activity code match ({org_data.get('activity_code', '')})"
        }
        
        return {
            'primary_reason': reason_mapping.get(primary_factor, primary_factor),
            'strength': strength,
            'total_score': total_score,
            'weighted_contributions': weighted_contributions,
            'qualification_details': qualification_details,
            'contributing_factors': [k for k, v in weighted_contributions.items() if v > 0.1]
        }
    
    def _classify_organization(self, org_data: Dict[str, Any], criteria: ClassificationCriteria) -> Dict[str, Any]:
        """Classify a single organization and calculate composite score."""
        name = org_data.get('name', '')
        
        # Calculate component scores
        keyword_scores = self._calculate_keyword_score(name, criteria)
        financial_score = self._calculate_financial_score(org_data, criteria)
        geographic_score = self._calculate_geographic_score(org_data, criteria)
        foundation_score = self._calculate_foundation_score(org_data, criteria)
        activity_score = self._calculate_activity_score(org_data, criteria)
        
        # Find best keyword category match
        best_category = max(keyword_scores, key=keyword_scores.get)
        best_keyword_score = keyword_scores[best_category]
        
        # Calculate composite score with weights
        weights = {
            'keyword': 0.35,
            'financial': 0.25,
            'geographic': 0.15,
            'foundation': 0.15,
            'activity': 0.10
        }
        
        composite_score = (
            weights['keyword'] * best_keyword_score +
            weights['financial'] * financial_score +
            weights['geographic'] * geographic_score +
            weights['foundation'] * foundation_score +
            weights['activity'] * activity_score
        )
        
        # NEW: Analyze qualification factors and primary qualifying reason
        qualification_factors = self._analyze_qualification_factors(
            keyword_scores, financial_score, geographic_score, 
            foundation_score, activity_score, weights, org_data
        )
        
        return {
            'ein': org_data.get('ein'),
            'name': name,
            'predicted_category': best_category,
            'keyword_scores': keyword_scores,
            'financial_score': financial_score,
            'geographic_score': geographic_score,
            'foundation_score': foundation_score,
            'activity_score': activity_score,
            'composite_score': composite_score,
            'classification_confidence': best_keyword_score,
            'assets': org_data.get('assets'),
            'revenue': org_data.get('revenue'),
            'city': org_data.get('city'),
            'state': org_data.get('state'),
            'zip': org_data.get('zip'),
            'foundation_code': org_data.get('foundation_code'),
            'activity_code': org_data.get('activity_code'),
            # NEW: Qualification analysis
            'qualification_factors': qualification_factors,
            'primary_qualification_reason': qualification_factors['primary_reason'],
            'qualification_strength': qualification_factors['strength']
        }
    
    async def _load_unclassified_organizations(self) -> List[Dict[str, Any]]:
        """Load organizations without NTEE codes from BMF database."""
        db_path = Path("data/nonprofit_intelligence.db")
        
        if not db_path.exists():
            raise FileNotFoundError(f"BMF database not found: {db_path}")
        
        unclassified_orgs = []
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Query for organizations without NTEE codes
            query = """
            SELECT DISTINCT
                ein, organization_name, city, state, zip_code,
                income_amount, asset_amount, classification,
                foundation_code, activity_codes, subsection_code
            FROM bmf_organizations 
            WHERE (ntee_code IS NULL OR ntee_code = '' OR TRIM(ntee_code) = '')
            AND ein IS NOT NULL 
            AND organization_name IS NOT NULL
            AND TRIM(ein) != ''
            AND TRIM(organization_name) != ''
            LIMIT 10000
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                ein, name, city, state, zip_code, income_amt, asset_amt, classification, foundation_code, activity_codes, subsection_code = row
                
                # Convert financial data
                revenue = None
                assets = None
                
                if income_amt and str(income_amt).replace('.', '').isdigit():
                    revenue = float(income_amt)
                
                if asset_amt and str(asset_amt).replace('.', '').isdigit():
                    assets = float(asset_amt)
                
                unclassified_orgs.append({
                    'ein': ein or '',
                    'name': name or '',
                    'city': city or '',
                    'state': state or '',
                    'zip': zip_code or '',
                    'revenue': revenue,
                    'assets': assets,
                    'classification': classification or '',
                    'foundation_code': foundation_code or '',
                    'activity_code': activity_codes or '',
                    'subsection_code': subsection_code or ''
                })
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error loading unclassified organizations from database: {e}")
            raise
        
        self.logger.info(f"Loaded {len(unclassified_orgs)} unclassified organizations")
        return unclassified_orgs
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute intelligent classification."""
        result = ProcessorResult(
            success=False,
            processor_name=self.metadata.name,
            start_time=datetime.now()
        )
        
        try:
            self.logger.info("Starting intelligent classification of unclassified organizations")
            
            # Load unclassified organizations
            self._update_progress(1, 5, "Loading unclassified organizations")
            unclassified_orgs = await self._load_unclassified_organizations()
            
            # Use default criteria (could be configurable in future)
            criteria = self.default_criteria
            
            # Classify organizations
            self._update_progress(2, 5, "Classifying organizations")
            classified_orgs = []
            
            for i, org_data in enumerate(unclassified_orgs):
                if i % 1000 == 0:
                    self._update_progress(
                        2, 5, 
                        f"Classified {i:,}/{len(unclassified_orgs):,} organizations"
                    )
                
                classification = self._classify_organization(org_data, criteria)
                classified_orgs.append(classification)
            
            # Sort by composite score
            self._update_progress(4, 5, "Ranking results")
            classified_orgs.sort(key=lambda x: x['composite_score'], reverse=True)
            
            # Filter promising candidates
            promising_candidates = [
                org for org in classified_orgs 
                if org['composite_score'] >= 0.3  # Configurable threshold
            ]
            
            # Store results
            result.add_data("classified_organizations", classified_orgs)
            result.add_data("promising_candidates", promising_candidates)
            result.add_data("total_unclassified", len(unclassified_orgs))
            result.add_data("promising_count", len(promising_candidates))
            
            # Add metadata
            result.add_metadata("classification_criteria", {
                "health_keywords_count": len(criteria.health_keywords),
                "nutrition_keywords_count": len(criteria.nutrition_keywords),
                "safety_keywords_count": len(criteria.safety_keywords),
                "min_composite_score": 0.3,
                "score_weights": {
                    "keyword": 0.35,
                    "financial": 0.25,
                    "geographic": 0.15,
                    "foundation": 0.15,
                    "activity": 0.10
                }
            })
            
            # Generate category breakdown
            category_breakdown = {}
            for org in promising_candidates:
                category = org['predicted_category']
                category_breakdown[category] = category_breakdown.get(category, 0) + 1
            
            result.add_metadata("category_breakdown", category_breakdown)
            
            self.logger.info(
                f"Classification complete: {len(promising_candidates)} promising candidates "
                f"from {len(unclassified_orgs)} unclassified organizations"
            )
            
            self._update_progress(5, 5, f"Found {len(promising_candidates)} promising candidates")
            result.success = True
        
        except Exception as e:
            self.logger.error(f"Classification failed: {str(e)}", exc_info=True)
            result.add_error(f"Classification error: {str(e)}")
        
        finally:
            result.end_time = datetime.now()
            if result.start_time and result.end_time:
                result.execution_time = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def cleanup(self, config: ProcessorConfig) -> None:
        """Clean up any temporary resources."""
        pass


# Register the processor
def register_processor():
    """Register this processor with the workflow engine."""
    from src.core.workflow_engine import get_workflow_engine
    
    engine = get_workflow_engine()
    engine.register_processor(IntelligentClassifier)
    
    return IntelligentClassifier


def get_processor():
    """Factory function for processor registration."""
    return IntelligentClassifier()