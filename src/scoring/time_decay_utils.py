"""
Time-Decay Utilities for 990-PF Screening Enhancement
Applies exponential decay to dated features to reduce noise from stale data.

Purpose: Foundation infrastructure for all time-sensitive scoring features
Lambda calibration:
  - λ=0.03/month for Schedule I grants (half-life ~23 months)
  - λ=0.02/month for NTEE/mission features (half-life ~35 months)
  - λ=0.04/month for website data (half-life ~17 months)

Created: Phase 1, Week 1 (990-PF Screening Enhancement)
"""

import math
from datetime import datetime, date
from typing import Union, Optional
from enum import Enum


class DecayType(str, Enum):
    """Decay rate presets for different feature types"""
    SCHEDULE_I_GRANTS = "schedule_i_grants"      # λ=0.03, half-life ~23 months
    NTEE_MISSION = "ntee_mission"                # λ=0.02, half-life ~35 months
    WEBSITE_DATA = "website_data"                # λ=0.04, half-life ~17 months
    FILING_DATA = "filing_data"                  # λ=0.025, half-life ~28 months
    CUSTOM = "custom"                            # User-specified λ


class TimeDecayCalculator:
    """
    Exponential time-decay calculator for aging 990-PF data features.

    Formula: weight = e^(-λ × months_old)

    Where:
    - λ (lambda) = decay rate parameter
    - months_old = time elapsed since reference date

    Example:
        >>> calculator = TimeDecayCalculator(decay_type=DecayType.SCHEDULE_I_GRANTS)
        >>> weight = calculator.calculate_decay(months_old=12)
        >>> print(f"Weight after 12 months: {weight:.3f}")
        Weight after 12 months: 0.698
    """

    # Decay rate mappings (λ values)
    DECAY_RATES = {
        DecayType.SCHEDULE_I_GRANTS: 0.03,
        DecayType.NTEE_MISSION: 0.02,
        DecayType.WEBSITE_DATA: 0.04,
        DecayType.FILING_DATA: 0.025,
    }

    def __init__(
        self,
        decay_type: DecayType = DecayType.SCHEDULE_I_GRANTS,
        custom_lambda: Optional[float] = None
    ):
        """
        Initialize time-decay calculator.

        Args:
            decay_type: Type of feature being decayed (determines λ)
            custom_lambda: Custom λ value (only used if decay_type=CUSTOM)
        """
        self.decay_type = decay_type

        if decay_type == DecayType.CUSTOM:
            if custom_lambda is None:
                raise ValueError("custom_lambda required when decay_type=CUSTOM")
            if custom_lambda <= 0:
                raise ValueError("custom_lambda must be positive")
            self.lambda_value = custom_lambda
        else:
            self.lambda_value = self.DECAY_RATES[decay_type]

    def calculate_decay(self, months_old: float) -> float:
        """
        Calculate exponential decay weight.

        Args:
            months_old: Time elapsed in months since reference date

        Returns:
            Decay multiplier in range [0, 1]
            - 1.0 = no decay (current data)
            - 0.5 = half-life reached
            - 0.0 = complete decay (asymptotic)

        Example:
            >>> calc = TimeDecayCalculator(DecayType.SCHEDULE_I_GRANTS)
            >>> calc.calculate_decay(0)    # Current data
            1.0
            >>> calc.calculate_decay(23)   # Approx half-life
            0.499
            >>> calc.calculate_decay(48)   # 4 years old
            0.237
        """
        if months_old < 0:
            raise ValueError("months_old cannot be negative")

        # Exponential decay: e^(-λt)
        decay_weight = math.exp(-self.lambda_value * months_old)

        return decay_weight

    def calculate_decay_from_date(
        self,
        reference_date: Union[datetime, date, str],
        current_date: Optional[Union[datetime, date]] = None
    ) -> float:
        """
        Calculate decay weight from reference date to current date.

        Args:
            reference_date: Date of the data (filing date, grant date, etc.)
            current_date: Current date for comparison (default: today)

        Returns:
            Decay multiplier in range [0, 1]

        Example:
            >>> calc = TimeDecayCalculator(DecayType.SCHEDULE_I_GRANTS)
            >>> filing_date = "2022-12-31"
            >>> weight = calc.calculate_decay_from_date(filing_date)
        """
        # Parse reference date
        if isinstance(reference_date, str):
            reference_date = datetime.fromisoformat(reference_date).date()
        elif isinstance(reference_date, datetime):
            reference_date = reference_date.date()

        # Set current date
        if current_date is None:
            current_date = datetime.now().date()
        elif isinstance(current_date, datetime):
            current_date = current_date.date()

        # Calculate months elapsed
        months_old = self._calculate_months_between(reference_date, current_date)

        # Apply decay
        return self.calculate_decay(months_old)

    def _calculate_months_between(self, start_date: date, end_date: date) -> float:
        """
        Calculate months between two dates with precision.

        Args:
            start_date: Earlier date
            end_date: Later date

        Returns:
            Months elapsed (fractional)
        """
        if end_date < start_date:
            raise ValueError("end_date must be >= start_date")

        # Year difference in months
        year_diff_months = (end_date.year - start_date.year) * 12

        # Month difference
        month_diff = end_date.month - start_date.month

        # Day fraction
        day_fraction = (end_date.day - start_date.day) / 30.0

        total_months = year_diff_months + month_diff + day_fraction

        return max(0.0, total_months)

    def get_half_life_months(self) -> float:
        """
        Calculate half-life for current decay rate.

        Returns:
            Months until weight = 0.5

        Formula: half_life = ln(2) / λ
        """
        return math.log(2) / self.lambda_value

    def apply_decay_to_score(
        self,
        base_score: float,
        months_old: float,
        min_weight: float = 0.0
    ) -> float:
        """
        Apply time-decay to a score value.

        Args:
            base_score: Original score without decay
            months_old: Age of data in months
            min_weight: Minimum decay weight (floor, default 0.0)

        Returns:
            Decayed score: base_score × max(decay_weight, min_weight)

        Example:
            >>> calc = TimeDecayCalculator(DecayType.SCHEDULE_I_GRANTS)
            >>> calc.apply_decay_to_score(base_score=10.0, months_old=24)
            4.87  # 10.0 × 0.487
        """
        decay_weight = self.calculate_decay(months_old)
        effective_weight = max(decay_weight, min_weight)

        return base_score * effective_weight

    def batch_calculate_decay(self, months_list: list[float]) -> list[float]:
        """
        Calculate decay weights for multiple time points.

        Args:
            months_list: List of months_old values

        Returns:
            List of decay weights

        Example:
            >>> calc = TimeDecayCalculator(DecayType.SCHEDULE_I_GRANTS)
            >>> calc.batch_calculate_decay([0, 12, 24, 36])
            [1.0, 0.698, 0.487, 0.340]
        """
        return [self.calculate_decay(months) for months in months_list]

    def get_decay_info(self) -> dict:
        """
        Get decay calculator configuration info.

        Returns:
            Dictionary with decay parameters and metrics
        """
        return {
            "decay_type": self.decay_type.value,
            "lambda": self.lambda_value,
            "half_life_months": round(self.get_half_life_months(), 2),
            "weight_at_12mo": round(self.calculate_decay(12), 3),
            "weight_at_24mo": round(self.calculate_decay(24), 3),
            "weight_at_36mo": round(self.calculate_decay(36), 3),
        }


# Convenience functions for common use cases

def apply_schedule_i_decay(base_score: float, grant_year: int) -> float:
    """
    Apply Schedule I grant decay (λ=0.03).

    Args:
        base_score: Original grant-based score
        grant_year: Year the grant was made

    Returns:
        Time-decayed score
    """
    calculator = TimeDecayCalculator(DecayType.SCHEDULE_I_GRANTS)
    current_year = datetime.now().year
    years_old = current_year - grant_year
    months_old = years_old * 12

    return calculator.apply_decay_to_score(base_score, months_old)


def apply_filing_decay(base_score: float, filing_date: Union[str, datetime, date]) -> float:
    """
    Apply 990-PF filing date decay (λ=0.025).

    Args:
        base_score: Original score
        filing_date: Filing date of 990-PF

    Returns:
        Time-decayed score
    """
    calculator = TimeDecayCalculator(DecayType.FILING_DATA)
    return calculator.apply_decay_to_score(
        base_score,
        calculator._calculate_months_between(
            datetime.fromisoformat(str(filing_date)).date() if isinstance(filing_date, str) else filing_date,
            datetime.now().date()
        )
    )


def apply_ntee_decay(base_score: float, filing_date: Union[str, datetime, date]) -> float:
    """
    Apply NTEE/mission data decay (λ=0.02, slower decay for stable features).

    Args:
        base_score: Original NTEE alignment score
        filing_date: Date of filing containing NTEE data

    Returns:
        Time-decayed score
    """
    calculator = TimeDecayCalculator(DecayType.NTEE_MISSION)

    if isinstance(filing_date, str):
        filing_date = datetime.fromisoformat(filing_date).date()
    elif isinstance(filing_date, datetime):
        filing_date = filing_date.date()

    months_old = calculator._calculate_months_between(filing_date, datetime.now().date())

    return calculator.apply_decay_to_score(base_score, months_old)


def get_decay_weight(
    reference_date: Union[str, datetime, date],
    decay_type: DecayType = DecayType.SCHEDULE_I_GRANTS
) -> float:
    """
    Get decay weight for a specific date.

    Args:
        reference_date: Date to calculate decay from
        decay_type: Type of decay to apply

    Returns:
        Decay weight [0, 1]
    """
    calculator = TimeDecayCalculator(decay_type)
    return calculator.calculate_decay_from_date(reference_date)
