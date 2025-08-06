#!/usr/bin/env python3
"""
Catalynx Predictive Success Modeling Engine
Advanced machine learning pipeline for opportunity success prediction
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import joblib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    success_probability: float
    confidence_score: float
    key_factors: List[str]
    risk_factors: List[str]
    predicted_timeline: Optional[int]
    recommendation: str

@dataclass
class ModelMetrics:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    feature_importance: Dict[str, float]
    training_date: datetime
    data_points: int

class PredictiveSuccessEngine:
    """Advanced predictive modeling for grant and opportunity success prediction"""
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or Path("models")
        self.model_path.mkdir(exist_ok=True)
        
        # ML Models
        self.success_classifier = RandomForestClassifier(
            n_estimators=200, max_depth=15, random_state=42
        )
        self.timeline_predictor = GradientBoostingRegressor(
            n_estimators=150, max_depth=8, random_state=42
        )
        
        # Preprocessing
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
        # Model metadata
        self.is_trained = False
        self.feature_columns = []
        self.metrics = None
        
        # Success factors configuration
        self.success_factors = {
            'financial_health': ['revenue_trend', 'financial_stability', 'growth_rate'],
            'organizational_fit': ['mission_alignment', 'program_match', 'geographic_overlap'],
            'network_strength': ['board_connections', 'influence_score', 'partnership_history'],
            'track_record': ['previous_grants', 'success_rate', 'completion_rate'],
            'capacity': ['staff_size', 'experience_level', 'resource_availability']
        }
        
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare and engineer features for prediction"""
        features = data.copy()
        
        # Financial health features
        features['revenue_growth'] = features.get('current_revenue', 0) / features.get('previous_revenue', 1)
        features['financial_stability'] = np.where(features['revenue_growth'] > 0.9, 1, 0)
        features['size_category'] = pd.cut(features.get('total_revenue', 0), 
                                         bins=[0, 100000, 500000, 2000000, float('inf')],
                                         labels=['small', 'medium', 'large', 'enterprise'])
        
        # Network and influence features
        features['network_score'] = (
            features.get('board_connections', 0) * 0.4 +
            features.get('partnership_count', 0) * 0.3 +
            features.get('influence_score', 0) * 0.3
        )
        
        # Historical success features
        features['success_rate'] = features.get('successful_grants', 0) / (features.get('total_grants', 1) + 1)
        features['experience_score'] = np.log1p(features.get('years_active', 0))
        
        # Composite features
        features['opportunity_fit'] = (
            features.get('mission_alignment', 0.5) * 0.4 +
            features.get('program_match', 0.5) * 0.4 +
            features.get('geographic_fit', 0.5) * 0.2
        )
        
        return features
    
    def train_model(self, training_data: pd.DataFrame, target_column: str = 'success') -> ModelMetrics:
        """Train the predictive success model"""
        logger.info("Starting predictive model training...")
        
        # Prepare features
        features = self.prepare_features(training_data)
        
        # Select feature columns (exclude target and identifiers)
        exclude_cols = [target_column, 'organization_id', 'grant_id', 'name', 'ein']
        self.feature_columns = [col for col in features.columns if col not in exclude_cols]
        
        X = features[self.feature_columns]
        y = features[target_column]
        
        # Handle categorical variables
        for col in X.select_dtypes(include=['object']).columns:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
            X[col] = self.label_encoders[col].fit_transform(X[col].astype(str))
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train success classifier
        self.success_classifier.fit(X_train_scaled, y_train)
        
        # Train timeline predictor (if timeline data available)
        if 'completion_days' in features.columns:
            timeline_data = features.dropna(subset=['completion_days'])
            if len(timeline_data) > 50:
                X_timeline = self.scaler.transform(timeline_data[self.feature_columns])
                y_timeline = timeline_data['completion_days']
                self.timeline_predictor.fit(X_timeline, y_timeline)
        
        # Evaluate model
        y_pred = self.success_classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')
        
        # Feature importance
        feature_importance = dict(zip(self.feature_columns, self.success_classifier.feature_importances_))
        
        # Save metrics
        self.metrics = ModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            feature_importance=feature_importance,
            training_date=datetime.now(),
            data_points=len(training_data)
        )
        
        self.is_trained = True
        self.save_model()
        
        logger.info(f"Model training complete. Accuracy: {accuracy:.3f}, F1: {f1:.3f}")
        return self.metrics
    
    def predict_success(self, opportunity_data: Dict[str, Any]) -> PredictionResult:
        """Predict success probability for an opportunity"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Convert to DataFrame
        df = pd.DataFrame([opportunity_data])
        features = self.prepare_features(df)
        
        # Prepare features for prediction
        X = features[self.feature_columns]
        
        # Handle categorical variables
        for col in X.select_dtypes(include=['object']).columns:
            if col in self.label_encoders:
                X[col] = self.label_encoders[col].transform(X[col].astype(str))
            else:
                X[col] = 0  # Default for unseen categories
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Predict success probability
        success_prob = self.success_classifier.predict_proba(X_scaled)[0, 1]
        
        # Calculate confidence based on feature importance and data quality
        confidence = self._calculate_confidence(features.iloc[0], success_prob)
        
        # Identify key success and risk factors
        key_factors = self._identify_key_factors(features.iloc[0], positive=True)
        risk_factors = self._identify_key_factors(features.iloc[0], positive=False)
        
        # Predict timeline if model is available
        predicted_timeline = None
        try:
            predicted_timeline = int(self.timeline_predictor.predict(X_scaled)[0])
        except:
            predicted_timeline = self._estimate_timeline(success_prob)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(success_prob, confidence, key_factors, risk_factors)
        
        return PredictionResult(
            success_probability=success_prob,
            confidence_score=confidence,
            key_factors=key_factors,
            risk_factors=risk_factors,
            predicted_timeline=predicted_timeline,
            recommendation=recommendation
        )
    
    def batch_predict(self, opportunities: List[Dict[str, Any]]) -> List[PredictionResult]:
        """Predict success for multiple opportunities efficiently"""
        return [self.predict_success(opp) for opp in opportunities]
    
    def _calculate_confidence(self, features: pd.Series, success_prob: float) -> float:
        """Calculate confidence score based on data quality and prediction certainty"""
        confidence_factors = []
        
        # Data completeness
        completeness = 1 - (features.isnull().sum() / len(features))
        confidence_factors.append(completeness * 0.3)
        
        # Prediction certainty (distance from 0.5)
        certainty = abs(success_prob - 0.5) * 2
        confidence_factors.append(certainty * 0.4)
        
        # Feature quality (based on importance)
        important_features = sorted(self.metrics.feature_importance.items(), 
                                  key=lambda x: x[1], reverse=True)[:5]
        feature_quality = sum(1 for feat, _ in important_features 
                            if feat in features.index and not pd.isnull(features[feat])) / 5
        confidence_factors.append(feature_quality * 0.3)
        
        return min(sum(confidence_factors), 1.0)
    
    def _identify_key_factors(self, features: pd.Series, positive: bool = True) -> List[str]:
        """Identify key success or risk factors"""
        if not self.metrics:
            return []
        
        # Get top important features
        sorted_features = sorted(self.metrics.feature_importance.items(), 
                               key=lambda x: x[1], reverse=True)
        
        factors = []
        for feature, importance in sorted_features[:10]:
            if feature in features.index:
                value = features[feature]
                if pd.isnull(value):
                    continue
                
                # Determine if this is a positive or negative factor
                is_positive = self._is_positive_factor(feature, value)
                
                if is_positive == positive:
                    factor_name = self._get_factor_description(feature, value)
                    factors.append(factor_name)
                
                if len(factors) >= 5:
                    break
        
        return factors
    
    def _is_positive_factor(self, feature: str, value: Any) -> bool:
        """Determine if a feature value is positive for success"""
        positive_indicators = {
            'revenue_growth': lambda x: x > 1.0,
            'financial_stability': lambda x: x == 1,
            'network_score': lambda x: x > 0.5,
            'success_rate': lambda x: x > 0.7,
            'opportunity_fit': lambda x: x > 0.6,
            'experience_score': lambda x: x > 1.0
        }
        
        if feature in positive_indicators:
            return positive_indicators[feature](value)
        
        # Default heuristics
        if isinstance(value, (int, float)):
            return value > 0.5 if 0 <= value <= 1 else value > 0
        
        return True
    
    def _get_factor_description(self, feature: str, value: Any) -> str:
        """Convert feature names to human-readable descriptions"""
        descriptions = {
            'revenue_growth': f"Revenue growth: {value:.1%}" if value > 1 else f"Revenue decline: {(1-value):.1%}",
            'financial_stability': "Strong financial stability" if value == 1 else "Financial instability concerns",
            'network_score': f"Strong network connections (score: {value:.2f})",
            'success_rate': f"High success rate: {value:.1%}",
            'opportunity_fit': f"Strong opportunity alignment: {value:.1%}",
            'experience_score': f"Extensive experience (score: {value:.1f})"
        }
        
        return descriptions.get(feature, f"{feature}: {value}")
    
    def _estimate_timeline(self, success_prob: float) -> int:
        """Estimate timeline based on success probability"""
        # Higher success probability typically means faster completion
        base_days = 180
        probability_factor = 1.5 - success_prob  # 0.5 to 1.5 range
        return int(base_days * probability_factor)
    
    def _generate_recommendation(self, success_prob: float, confidence: float, 
                               key_factors: List[str], risk_factors: List[str]) -> str:
        """Generate actionable recommendation"""
        if success_prob >= 0.8 and confidence >= 0.7:
            return "Highly Recommended: Excellent success probability with high confidence"
        elif success_prob >= 0.6 and confidence >= 0.6:
            return "Recommended: Good success potential, monitor risk factors"
        elif success_prob >= 0.4:
            return "Conditional: Medium potential, address key risk factors before proceeding"
        else:
            return "Not Recommended: Low success probability, significant improvements needed"
    
    def get_model_insights(self) -> Dict[str, Any]:
        """Get insights about the trained model"""
        if not self.metrics:
            return {"error": "Model not trained"}
        
        return {
            "model_performance": {
                "accuracy": self.metrics.accuracy,
                "precision": self.metrics.precision,
                "recall": self.metrics.recall,
                "f1_score": self.metrics.f1_score
            },
            "top_features": sorted(self.metrics.feature_importance.items(), 
                                 key=lambda x: x[1], reverse=True)[:10],
            "training_info": {
                "training_date": self.metrics.training_date.isoformat(),
                "data_points": self.metrics.data_points,
                "feature_count": len(self.feature_columns)
            }
        }
    
    def save_model(self):
        """Save trained model to disk"""
        if not self.is_trained:
            return
        
        model_data = {
            'success_classifier': self.success_classifier,
            'timeline_predictor': self.timeline_predictor,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
            'metrics': self.metrics
        }
        
        joblib.dump(model_data, self.model_path / "predictive_model.joblib")
        logger.info(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model from disk"""
        model_file = self.model_path / "predictive_model.joblib"
        if not model_file.exists():
            logger.warning("No saved model found")
            return False
        
        try:
            model_data = joblib.load(model_file)
            self.success_classifier = model_data['success_classifier']
            self.timeline_predictor = model_data['timeline_predictor']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.feature_columns = model_data['feature_columns']
            self.metrics = model_data['metrics']
            self.is_trained = True
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

# Global instance
predictive_engine = PredictiveSuccessEngine()