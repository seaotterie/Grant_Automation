"""
Gold Set Evaluation Framework
Infrastructure for creating, labeling, and validating 990-PF screening accuracy.

Purpose: Empirical validation of scoring improvements
Timeline: Phase 1 Week 1 (creation) through Phase 5 Week 10 (final validation)
Target Metrics: F1 ≥0.75, P@10 ≥0.80, ECE ≤0.10

Created: Phase 1, Week 1
"""

import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np


class MatchLabel(str, Enum):
    """Expert labeling categories for profile-foundation pairs"""
    STRONG_MATCH = "match"           # Clear alignment, high probability of success
    NO_MATCH = "no_match"            # Clear misalignment, low probability
    UNCERTAIN = "uncertain"           # Borderline case, requires deeper analysis


class SamplingStrategy(str, Enum):
    """Strategies for sampling gold set pairs"""
    RANDOM = "random"                # Random sampling across score range
    STRATIFIED = "stratified"        # Stratified by score bands
    EDGE_CASES = "edge_cases"        # Focus on difficult/conflicting cases
    HIGH_VOLUME = "high_volume"      # Sample from high-opportunity-count profiles


@dataclass
class ProfileFoundationPair:
    """A single profile-foundation pair for labeling"""
    pair_id: str
    profile_ein: str
    profile_name: str
    profile_ntee: str
    profile_state: str
    profile_revenue: Optional[float]

    foundation_ein: str
    foundation_name: str
    foundation_ntee: Optional[str]
    foundation_state: str
    foundation_assets: Optional[float]

    # Scoring metadata
    predicted_score: float            # Model's compatibility score
    score_band: str                  # "high", "medium", "low", "borderline"

    # Labeling
    expert_label: Optional[MatchLabel] = None
    expert_notes: Optional[str] = None
    labeled_by: Optional[str] = None
    labeled_at: Optional[str] = None

    # Additional context
    schedule_i_grantees: List[str] = field(default_factory=list)
    geographic_overlap: bool = False
    ntee_major_match: bool = False
    ntee_leaf_match: bool = False
    has_conflicts: bool = False
    conflict_reasons: List[str] = field(default_factory=list)

    # Metadata
    sampling_strategy: str = "random"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GoldSetMetrics:
    """Evaluation metrics for gold set validation"""
    # Basic counts
    total_pairs: int
    labeled_pairs: int
    unlabeled_pairs: int

    # Label distribution
    strong_matches: int
    no_matches: int
    uncertain: int

    # Model performance (after evaluation)
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None

    # Ranking metrics
    precision_at_10: Optional[float] = None
    precision_at_50: Optional[float] = None
    top_2_accuracy: Optional[float] = None

    # Calibration
    expected_calibration_error: Optional[float] = None

    # Inter-rater agreement (if multiple labelers)
    cohens_kappa: Optional[float] = None

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    evaluated_at: Optional[str] = None


class GoldSetEvaluator:
    """
    Gold set creation, labeling, and evaluation infrastructure.

    Workflow:
    1. Sample profile-foundation pairs (1,500 total)
    2. Expert labeling (250-300 hours effort)
    3. Model evaluation (F1, P@K, calibration)
    4. Threshold calibration
    5. Drift monitoring over time
    """

    def __init__(self, gold_set_dir: str = "data/evaluation/gold_set"):
        """
        Initialize gold set evaluator.

        Args:
            gold_set_dir: Directory for gold set storage
        """
        self.gold_set_dir = Path(gold_set_dir)
        self.gold_set_dir.mkdir(parents=True, exist_ok=True)

        self.pairs_file = self.gold_set_dir / "gold_set_pairs.json"
        self.metrics_file = self.gold_set_dir / "gold_set_metrics.json"
        self.logger = logging.getLogger(__name__)

        self.pairs: List[ProfileFoundationPair] = []
        self.metrics: Optional[GoldSetMetrics] = None

        # Load existing if available
        self._load_gold_set()

    # =========================================================================
    # PHASE 1: GOLD SET CREATION (Week 1)
    # =========================================================================

    def create_gold_set(
        self,
        total_pairs: int = 1500,
        stratification: Dict[str, int] = None
    ) -> List[ProfileFoundationPair]:
        """
        Create gold set by sampling profile-foundation pairs.

        Recommended stratification:
        - 300 obvious matches (high scores, clear alignment)
        - 600 borderline cases (0.50-0.70 score range)
        - 300 obvious non-matches (low scores, misalignment)
        - 300 edge cases (conflicts, sparse data, mission shift)

        Args:
            total_pairs: Total number of pairs to sample
            stratification: Distribution across categories

        Returns:
            List of sampled pairs ready for labeling
        """
        if stratification is None:
            stratification = {
                "obvious_matches": 300,
                "borderline": 600,
                "obvious_non_matches": 300,
                "edge_cases": 300,
            }

        self.logger.info(f"Creating gold set with {total_pairs} pairs")
        self.logger.info(f"Stratification: {stratification}")

        sampled_pairs = []

        # Sample each category
        for category, count in stratification.items():
            self.logger.info(f"Sampling {count} {category} pairs...")
            category_pairs = self._sample_category(category, count)
            sampled_pairs.extend(category_pairs)

        self.pairs = sampled_pairs
        self._save_gold_set()

        self.logger.info(f"Gold set created with {len(self.pairs)} pairs")
        return self.pairs

    def _sample_category(self, category: str, count: int) -> List[ProfileFoundationPair]:
        """
        Sample pairs for a specific category.

        NOTE: This is a placeholder that creates mock data.
        In production, this would:
        1. Query BMF/SOI database for real foundations
        2. Query profiles database for real organizations
        3. Run current scorer to get predicted scores
        4. Sample based on score ranges and characteristics
        """
        pairs = []

        for i in range(count):
            # Create mock pair (replace with real data sampling)
            pair = self._create_mock_pair(category, i)
            pairs.append(pair)

        return pairs

    def _create_mock_pair(self, category: str, index: int) -> ProfileFoundationPair:
        """Create mock pair for testing (replace with real sampling)"""

        # Score ranges by category
        score_ranges = {
            "obvious_matches": (0.75, 0.95),
            "borderline": (0.50, 0.70),
            "obvious_non_matches": (0.10, 0.40),
            "edge_cases": (0.45, 0.75),  # Wide range with conflicts
        }

        score_range = score_ranges.get(category, (0.30, 0.70))
        predicted_score = random.uniform(*score_range)

        # Determine score band
        if predicted_score >= 0.70:
            score_band = "high"
        elif predicted_score >= 0.58:
            score_band = "medium"
        elif predicted_score >= 0.50:
            score_band = "borderline"
        else:
            score_band = "low"

        return ProfileFoundationPair(
            pair_id=f"{category}_{index:04d}",
            profile_ein=f"30{random.randint(1000000, 9999999)}",
            profile_name=f"Mock Profile {index}",
            profile_ntee=random.choice(["P20", "B25", "E21", "P84", "F30"]),
            profile_state=random.choice(["VA", "MD", "DC", "NY", "CA"]),
            profile_revenue=random.randint(100000, 5000000),
            foundation_ein=f"54{random.randint(1000000, 9999999)}",
            foundation_name=f"Mock Foundation {index}",
            foundation_ntee=random.choice(["P20", "B25", "E21", "P84", "F30", None]),
            foundation_state=random.choice(["VA", "MD", "DC", "NY", "CA"]),
            foundation_assets=random.randint(1000000, 50000000),
            predicted_score=predicted_score,
            score_band=score_band,
            has_conflicts=(category == "edge_cases"),
            conflict_reasons=["mission_shift", "policy_conflict"] if category == "edge_cases" else [],
            sampling_strategy=category,
        )

    # =========================================================================
    # PHASE 2: LABELING WORKFLOW (Week 1-10)
    # =========================================================================

    def get_unlabeled_pairs(
        self,
        limit: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[ProfileFoundationPair]:
        """
        Get unlabeled pairs for expert review.

        Args:
            limit: Maximum pairs to return
            category: Filter by sampling category

        Returns:
            List of unlabeled pairs
        """
        unlabeled = [p for p in self.pairs if p.expert_label is None]

        if category:
            unlabeled = [p for p in unlabeled if p.sampling_strategy == category]

        if limit:
            unlabeled = unlabeled[:limit]

        return unlabeled

    def label_pair(
        self,
        pair_id: str,
        label: MatchLabel,
        labeler_name: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Add expert label to a pair.

        Args:
            pair_id: ID of pair to label
            label: Expert's match assessment
            labeler_name: Name/ID of labeler
            notes: Optional notes explaining decision

        Returns:
            True if successful, False if pair not found
        """
        for pair in self.pairs:
            if pair.pair_id == pair_id:
                pair.expert_label = label
                pair.expert_notes = notes
                pair.labeled_by = labeler_name
                pair.labeled_at = datetime.now().isoformat()

                self._save_gold_set()
                self.logger.info(f"Labeled pair {pair_id} as {label.value} by {labeler_name}")
                return True

        self.logger.warning(f"Pair {pair_id} not found")
        return False

    def get_labeling_progress(self) -> Dict[str, Any]:
        """
        Get current labeling progress statistics.

        Returns:
            Dictionary with progress metrics
        """
        total = len(self.pairs)
        labeled = sum(1 for p in self.pairs if p.expert_label is not None)
        unlabeled = total - labeled

        # Distribution by label
        strong_matches = sum(1 for p in self.pairs if p.expert_label == MatchLabel.STRONG_MATCH)
        no_matches = sum(1 for p in self.pairs if p.expert_label == MatchLabel.NO_MATCH)
        uncertain = sum(1 for p in self.pairs if p.expert_label == MatchLabel.UNCERTAIN)

        # Progress by category
        by_category = {}
        for pair in self.pairs:
            category = pair.sampling_strategy
            if category not in by_category:
                by_category[category] = {"total": 0, "labeled": 0}
            by_category[category]["total"] += 1
            if pair.expert_label is not None:
                by_category[category]["labeled"] += 1

        # Estimated time remaining (10 min per pair average)
        est_hours_remaining = (unlabeled * 10) / 60

        return {
            "total_pairs": total,
            "labeled": labeled,
            "unlabeled": unlabeled,
            "percent_complete": round(100 * labeled / total, 1) if total > 0 else 0,
            "label_distribution": {
                "strong_matches": strong_matches,
                "no_matches": no_matches,
                "uncertain": uncertain,
            },
            "by_category": by_category,
            "estimated_hours_remaining": round(est_hours_remaining, 1),
        }

    # =========================================================================
    # PHASE 3: EVALUATION (Week 9-10)
    # =========================================================================

    def evaluate_model(
        self,
        score_threshold: float = 0.58
    ) -> GoldSetMetrics:
        """
        Evaluate model performance on labeled gold set.

        Calculates:
        - Classification metrics (F1, precision, recall)
        - Ranking metrics (P@10, P@50, top-2 accuracy)
        - Calibration (ECE)

        Args:
            score_threshold: Threshold for binary classification

        Returns:
            GoldSetMetrics with all evaluation results
        """
        labeled_pairs = [p for p in self.pairs if p.expert_label is not None]

        if not labeled_pairs:
            raise ValueError("No labeled pairs available for evaluation")

        self.logger.info(f"Evaluating on {len(labeled_pairs)} labeled pairs")

        # Convert labels to binary (match vs no-match, exclude uncertain)
        y_true = []
        y_pred = []
        y_scores = []

        for pair in labeled_pairs:
            if pair.expert_label == MatchLabel.UNCERTAIN:
                continue  # Skip uncertain cases for binary metrics

            # True label: 1 for match, 0 for no-match
            y_true.append(1 if pair.expert_label == MatchLabel.STRONG_MATCH else 0)

            # Predicted label based on threshold
            y_pred.append(1 if pair.predicted_score >= score_threshold else 0)

            # Predicted score for ranking/calibration
            y_scores.append(pair.predicted_score)

        # Calculate metrics
        accuracy = self._calculate_accuracy(y_true, y_pred)
        precision = self._calculate_precision(y_true, y_pred)
        recall = self._calculate_recall(y_true, y_pred)
        f1 = self._calculate_f1(precision, recall)

        p_at_10 = self._calculate_precision_at_k(labeled_pairs, k=10)
        p_at_50 = self._calculate_precision_at_k(labeled_pairs, k=50)
        top_2_acc = self._calculate_top_k_accuracy(labeled_pairs, k=2)

        ece = self._calculate_expected_calibration_error(y_true, y_scores)

        # Create metrics object
        metrics = GoldSetMetrics(
            total_pairs=len(self.pairs),
            labeled_pairs=len(labeled_pairs),
            unlabeled_pairs=len(self.pairs) - len(labeled_pairs),
            strong_matches=sum(1 for p in labeled_pairs if p.expert_label == MatchLabel.STRONG_MATCH),
            no_matches=sum(1 for p in labeled_pairs if p.expert_label == MatchLabel.NO_MATCH),
            uncertain=sum(1 for p in labeled_pairs if p.expert_label == MatchLabel.UNCERTAIN),
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            precision_at_10=p_at_10,
            precision_at_50=p_at_50,
            top_2_accuracy=top_2_acc,
            expected_calibration_error=ece,
            evaluated_at=datetime.now().isoformat(),
        )

        self.metrics = metrics
        self._save_metrics()

        self.logger.info(f"Evaluation complete: F1={f1:.3f}, P@10={p_at_10:.3f}, ECE={ece:.3f}")

        return metrics

    # Helper metric calculations

    def _calculate_accuracy(self, y_true: List[int], y_pred: List[int]) -> float:
        """Calculate classification accuracy"""
        correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
        return correct / len(y_true) if y_true else 0.0

    def _calculate_precision(self, y_true: List[int], y_pred: List[int]) -> float:
        """Calculate precision"""
        true_positives = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 1)
        predicted_positives = sum(y_pred)
        return true_positives / predicted_positives if predicted_positives > 0 else 0.0

    def _calculate_recall(self, y_true: List[int], y_pred: List[int]) -> float:
        """Calculate recall"""
        true_positives = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 1)
        actual_positives = sum(y_true)
        return true_positives / actual_positives if actual_positives > 0 else 0.0

    def _calculate_f1(self, precision: float, recall: float) -> float:
        """Calculate F1 score"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    def _calculate_precision_at_k(
        self,
        labeled_pairs: List[ProfileFoundationPair],
        k: int
    ) -> float:
        """Calculate precision at top K ranked results"""
        # Sort by predicted score
        sorted_pairs = sorted(labeled_pairs, key=lambda p: p.predicted_score, reverse=True)
        top_k = sorted_pairs[:k]

        # Count matches in top K
        matches = sum(1 for p in top_k if p.expert_label == MatchLabel.STRONG_MATCH)

        return matches / k if k > 0 else 0.0

    def _calculate_top_k_accuracy(
        self,
        labeled_pairs: List[ProfileFoundationPair],
        k: int
    ) -> float:
        """Calculate top-K accuracy (is correct match in top K results?)"""
        # Group by profile (simulating search results per profile)
        # For gold set, we treat each pair independently
        # This is a simplified version - in production, group by profile_ein

        sorted_pairs = sorted(labeled_pairs, key=lambda p: p.predicted_score, reverse=True)
        top_k = sorted_pairs[:k]

        has_match = any(p.expert_label == MatchLabel.STRONG_MATCH for p in top_k)

        return 1.0 if has_match else 0.0

    def _calculate_expected_calibration_error(
        self,
        y_true: List[int],
        y_scores: List[float],
        n_bins: int = 10
    ) -> float:
        """
        Calculate Expected Calibration Error (ECE).

        Measures how well predicted probabilities match actual outcomes.
        Lower is better (target: <0.10).
        """
        if not y_true or not y_scores:
            return 0.0

        # Create bins
        bins = np.linspace(0, 1, n_bins + 1)

        ece = 0.0
        total_samples = len(y_true)

        for i in range(n_bins):
            # Find samples in this bin
            bin_lower = bins[i]
            bin_upper = bins[i + 1]

            bin_indices = [
                j for j, score in enumerate(y_scores)
                if bin_lower <= score < bin_upper or (i == n_bins - 1 and score == bin_upper)
            ]

            if not bin_indices:
                continue

            # Average predicted probability in bin
            bin_pred = np.mean([y_scores[j] for j in bin_indices])

            # Actual accuracy in bin
            bin_true = np.mean([y_true[j] for j in bin_indices])

            # Bin weight
            bin_weight = len(bin_indices) / total_samples

            # Contribution to ECE
            ece += bin_weight * abs(bin_pred - bin_true)

        return ece

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _save_gold_set(self):
        """Save gold set pairs to file"""
        try:
            data = [asdict(pair) for pair in self.pairs]
            with open(self.pairs_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Saved {len(self.pairs)} pairs to {self.pairs_file}")
        except Exception as e:
            self.logger.error(f"Failed to save gold set: {e}")

    def _save_metrics(self):
        """Save evaluation metrics to file"""
        if self.metrics:
            try:
                with open(self.metrics_file, 'w') as f:
                    json.dump(asdict(self.metrics), f, indent=2)
                self.logger.info(f"Saved metrics to {self.metrics_file}")
            except Exception as e:
                self.logger.error(f"Failed to save metrics: {e}")

    def _load_gold_set(self):
        """Load existing gold set if available"""
        if self.pairs_file.exists():
            try:
                with open(self.pairs_file, 'r') as f:
                    data = json.load(f)

                self.pairs = [
                    ProfileFoundationPair(
                        **{k: MatchLabel(v) if k == 'expert_label' and v else v
                           for k, v in pair.items()}
                    )
                    for pair in data
                ]

                self.logger.info(f"Loaded {len(self.pairs)} pairs from {self.pairs_file}")
            except Exception as e:
                self.logger.error(f"Failed to load gold set: {e}")

        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    metrics_data = json.load(f)
                self.metrics = GoldSetMetrics(**metrics_data)
                self.logger.info("Loaded existing metrics")
            except Exception as e:
                self.logger.error(f"Failed to load metrics: {e}")


# Convenience functions

def create_gold_set(output_dir: str = "data/evaluation/gold_set") -> GoldSetEvaluator:
    """
    Create and initialize a new gold set.

    Args:
        output_dir: Directory for gold set storage

    Returns:
        GoldSetEvaluator instance with sampled pairs
    """
    evaluator = GoldSetEvaluator(output_dir)
    evaluator.create_gold_set(total_pairs=1500)
    return evaluator


def get_labeling_status(gold_set_dir: str = "data/evaluation/gold_set") -> Dict:
    """
    Get current labeling progress.

    Args:
        gold_set_dir: Directory containing gold set

    Returns:
        Progress statistics
    """
    evaluator = GoldSetEvaluator(gold_set_dir)
    return evaluator.get_labeling_progress()
