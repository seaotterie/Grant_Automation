#!/usr/bin/env python3
"""
Catalynx Model Training and Validation System
Automated model training, validation, and performance monitoring
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
from dataclasses import dataclass, asdict

from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, validation_curve
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns

from .predictive_engine import PredictiveSuccessEngine, predictive_engine
from .success_scorer import SuccessScorer, success_scorer

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    cross_val_scores: List[float]
    mean_cv_score: float
    std_cv_score: float
    test_accuracy: float
    classification_report: Dict[str, Any]
    confusion_matrix: List[List[int]]
    roc_auc: float
    validation_date: datetime

@dataclass
class TrainingMetrics:
    training_time: float
    data_points: int
    feature_count: int
    model_size_mb: float
    convergence_iterations: int
    best_parameters: Dict[str, Any]

class ModelTrainer:
    """Advanced model training and validation system"""
    
    def __init__(self, results_path: Optional[Path] = None):
        self.results_path = results_path or Path("model_results")
        self.results_path.mkdir(exist_ok=True)
        
        self.engine = predictive_engine
        self.scorer = success_scorer
        
        # Training configuration
        self.param_grids = {
            'random_forest': {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 15, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            },
            'gradient_boosting': {
                'n_estimators': [100, 200],
                'max_depth': [3, 5, 8],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 1.0]
            }
        }
        
        # Validation settings
        self.cv_folds = 5
        self.test_size = 0.2
        
    def prepare_synthetic_training_data(self, size: int = 1000) -> pd.DataFrame:
        """Generate synthetic training data for demonstration"""
        np.random.seed(42)
        
        data = []
        for i in range(size):
            # Generate realistic organizational data
            revenue = np.random.lognormal(12, 1.5)  # $150K to $10M range
            years_active = np.random.randint(1, 25)
            staff_count = max(1, int(np.random.lognormal(2, 1)))  # 1 to 50 staff
            
            # Generate correlated features
            financial_stability = min(1.0, 0.3 + np.random.beta(2, 5) + (revenue > 500000) * 0.3)
            success_rate = min(1.0, 0.2 + financial_stability * 0.4 + np.random.beta(3, 2) * 0.4)
            
            # Network features
            board_connections = np.random.poisson(3) + (revenue > 1000000) * np.random.poisson(5)
            partnerships = np.random.poisson(2) + (years_active > 5) * np.random.poisson(3)
            
            # Calculate success probability based on features
            success_prob = (
                financial_stability * 0.3 +
                min(1.0, success_rate) * 0.25 +
                min(1.0, np.log(revenue) / 15) * 0.2 +
                min(1.0, board_connections / 10) * 0.15 +
                min(1.0, years_active / 20) * 0.1
            )
            
            # Add noise and determine success
            success_prob += np.random.normal(0, 0.1)
            success_prob = max(0, min(1, success_prob))
            success = 1 if np.random.random() < success_prob else 0
            
            data.append({
                'organization_id': f'org_{i:04d}',
                'total_revenue': revenue,
                'current_revenue': revenue,
                'previous_revenue': revenue * np.random.uniform(0.8, 1.2),
                'years_active': years_active,
                'staff_count': staff_count,
                'board_size': max(3, staff_count // 3 + np.random.poisson(2)),
                'avg_leadership_experience': np.random.uniform(2, 15),
                'program_areas': np.random.choice(['health', 'education', 'environment', 'arts'], 
                                                size=np.random.randint(1, 4), replace=False).tolist(),
                'board_connections': board_connections,
                'active_partnerships': [f'partner_{j}' for j in range(partnerships)],
                'total_grants_received': max(1, np.random.poisson(5) + years_active // 3),
                'successful_grants': None,  # Will be calculated
                'mission_alignment_score': np.random.beta(3, 2),
                'success': success
            })
        
        df = pd.DataFrame(data)
        
        # Calculate derived features
        df['successful_grants'] = (df['total_grants_received'] * 
                                  (0.3 + df['success'] * 0.4 + np.random.uniform(-0.2, 0.2, len(df)))).astype(int)
        df['successful_grants'] = df[['successful_grants', 'total_grants_received']].min(axis=1)
        
        return df
    
    def train_and_validate_model(self, training_data: Optional[pd.DataFrame] = None, 
                               use_grid_search: bool = True) -> Tuple[ValidationResult, TrainingMetrics]:
        """Train model with comprehensive validation"""
        if training_data is None:
            logger.info("Generating synthetic training data...")
            training_data = self.prepare_synthetic_training_data(1500)
        
        start_time = datetime.now()
        
        # Train the model
        logger.info("Training predictive model...")
        metrics = self.engine.train_model(training_data)
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Prepare data for validation
        features = self.engine.prepare_features(training_data)
        X = features[self.engine.feature_columns]
        y = features['success']
        
        # Handle categorical variables
        for col in X.select_dtypes(include=['object']).columns:
            if col in self.engine.label_encoders:
                X[col] = self.engine.label_encoders[col].transform(X[col].astype(str))
        
        X_scaled = self.engine.scaler.transform(X)
        
        # Cross-validation
        logger.info("Performing cross-validation...")
        cv_scores = self._perform_cross_validation(X_scaled, y)
        
        # Test set validation
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
        
        y_pred = self.engine.success_classifier.predict(X_test)
        y_pred_proba = self.engine.success_classifier.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        test_accuracy = (y_pred == y_test).mean()
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        # Classification report
        from sklearn.metrics import classification_report
        class_report = classification_report(y_test, y_pred, output_dict=True)
        
        # Confusion matrix
        conf_matrix = confusion_matrix(y_test, y_pred).tolist()
        
        # Training metrics
        model_size = self._calculate_model_size()
        
        validation_result = ValidationResult(
            cross_val_scores=cv_scores,
            mean_cv_score=np.mean(cv_scores),
            std_cv_score=np.std(cv_scores),
            test_accuracy=test_accuracy,
            classification_report=class_report,
            confusion_matrix=conf_matrix,
            roc_auc=roc_auc,
            validation_date=datetime.now()
        )
        
        training_metrics = TrainingMetrics(
            training_time=training_time,
            data_points=len(training_data),
            feature_count=len(self.engine.feature_columns),
            model_size_mb=model_size,
            convergence_iterations=getattr(self.engine.success_classifier, 'n_iter_', 100),
            best_parameters=self._get_best_parameters()
        )
        
        # Save results
        self._save_validation_results(validation_result, training_metrics)
        
        logger.info(f"Model validation complete. CV Score: {validation_result.mean_cv_score:.3f} ± {validation_result.std_cv_score:.3f}")
        logger.info(f"Test Accuracy: {validation_result.test_accuracy:.3f}, ROC AUC: {validation_result.roc_auc:.3f}")
        
        return validation_result, training_metrics
    
    def _perform_cross_validation(self, X: np.ndarray, y: np.ndarray) -> List[float]:
        """Perform cross-validation with time series split if applicable"""
        from sklearn.model_selection import cross_val_score
        
        # Use TimeSeriesSplit for temporal data, otherwise use standard CV
        cv = TimeSeriesSplit(n_splits=self.cv_folds)
        scores = cross_val_score(self.engine.success_classifier, X, y, cv=cv, scoring='accuracy')
        
        return scores.tolist()
    
    def hyperparameter_tuning(self, training_data: pd.DataFrame, model_type: str = 'random_forest') -> Dict[str, Any]:
        """Perform hyperparameter tuning"""
        if model_type not in self.param_grids:
            raise ValueError(f"Unknown model type: {model_type}")
        
        logger.info(f"Starting hyperparameter tuning for {model_type}...")
        
        # Prepare data
        features = self.engine.prepare_features(training_data)
        X = features[self.engine.feature_columns]
        y = features['success']
        
        # Handle categorical variables
        for col in X.select_dtypes(include=['object']).columns:
            if col in self.engine.label_encoders:
                X[col] = self.engine.label_encoders[col].transform(X[col].astype(str))
        
        X_scaled = self.engine.scaler.transform(X)
        
        # Grid search
        param_grid = self.param_grids[model_type]
        
        if model_type == 'random_forest':
            from sklearn.ensemble import RandomForestClassifier
            estimator = RandomForestClassifier(random_state=42)
        else:
            from sklearn.ensemble import GradientBoostingClassifier
            estimator = GradientBoostingClassifier(random_state=42)
        
        grid_search = GridSearchCV(
            estimator, param_grid, cv=self.cv_folds, 
            scoring='accuracy', n_jobs=-1, verbose=1
        )
        
        grid_search.fit(X_scaled, y)
        
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best CV score: {grid_search.best_score_:.3f}")
        
        return {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'cv_results': grid_search.cv_results_
        }
    
    def validate_scoring_system(self, test_data: pd.DataFrame) -> Dict[str, Any]:
        """Validate the success scoring system"""
        logger.info("Validating success scoring system...")
        
        validation_results = []
        
        for _, row in test_data.iterrows():
            org_data = row.to_dict()
            
            # Calculate success score
            success_score = self.scorer.calculate_success_score(org_data)
            
            # Get actual success if available
            actual_success = org_data.get('success', None)
            
            validation_results.append({
                'organization_id': org_data.get('organization_id', 'unknown'),
                'predicted_score': success_score.overall_score,
                'actual_success': actual_success,
                'confidence': success_score.confidence_level,
                'dimension_scores': success_score.dimension_scores
            })
        
        # Calculate scoring accuracy
        valid_predictions = [r for r in validation_results if r['actual_success'] is not None]
        
        if valid_predictions:
            # Convert scores to binary predictions
            score_threshold = 0.6
            predicted_binary = [1 if r['predicted_score'] > score_threshold else 0 for r in valid_predictions]
            actual_binary = [r['actual_success'] for r in valid_predictions]
            
            accuracy = sum(p == a for p, a in zip(predicted_binary, actual_binary)) / len(predicted_binary)
            
            # Calculate correlation
            scores = [r['predicted_score'] for r in valid_predictions]
            actual = [r['actual_success'] for r in valid_predictions]
            correlation = np.corrcoef(scores, actual)[0, 1] if len(scores) > 1 else 0
        else:
            accuracy = None
            correlation = None
        
        return {
            'validation_results': validation_results,
            'scoring_accuracy': accuracy,
            'score_correlation': correlation,
            'total_validated': len(validation_results),
            'validation_date': datetime.now().isoformat()
        }
    
    def _calculate_model_size(self) -> float:
        """Calculate model size in MB"""
        import pickle
        import io
        
        buffer = io.BytesIO()
        pickle.dump(self.engine.success_classifier, buffer)
        size_bytes = buffer.tell()
        
        return size_bytes / (1024 * 1024)  # Convert to MB
    
    def _get_best_parameters(self) -> Dict[str, Any]:
        """Get current model parameters"""
        return self.engine.success_classifier.get_params()
    
    def _save_validation_results(self, validation_result: ValidationResult, 
                               training_metrics: TrainingMetrics):
        """Save validation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {
            'validation': asdict(validation_result),
            'training_metrics': asdict(training_metrics),
            'model_info': self.engine.get_model_insights()
        }
        
        # Convert datetime objects to strings for JSON serialization
        results['validation']['validation_date'] = validation_result.validation_date.isoformat()
        
        results_file = self.results_path / f"validation_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Validation results saved to {results_file}")
    
    def generate_model_report(self) -> Dict[str, Any]:
        """Generate comprehensive model performance report"""
        if not self.engine.is_trained:
            return {"error": "Model not trained"}
        
        insights = self.engine.get_model_insights()
        
        # Load recent validation results
        recent_results = self._load_recent_validation_results()
        
        report = {
            "model_status": {
                "is_trained": self.engine.is_trained,
                "training_date": insights.get("training_info", {}).get("training_date"),
                "data_points": insights.get("training_info", {}).get("data_points"),
                "feature_count": insights.get("training_info", {}).get("feature_count")
            },
            "performance_metrics": insights.get("model_performance", {}),
            "top_features": insights.get("top_features", []),
            "recent_validation": recent_results,
            "recommendations": self._generate_model_recommendations(insights, recent_results)
        }
        
        return report
    
    def _load_recent_validation_results(self) -> Optional[Dict[str, Any]]:
        """Load most recent validation results"""
        result_files = list(self.results_path.glob("validation_results_*.json"))
        
        if not result_files:
            return None
        
        # Get most recent file
        latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load validation results: {e}")
            return None
    
    def _generate_model_recommendations(self, insights: Dict[str, Any], 
                                      validation_results: Optional[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for model improvement"""
        recommendations = []
        
        performance = insights.get("model_performance", {})
        accuracy = performance.get("accuracy", 0)
        
        if accuracy < 0.8:
            recommendations.append("Model accuracy is below 80%. Consider collecting more training data or feature engineering.")
        
        if accuracy < 0.7:
            recommendations.append("Model accuracy is critically low. Review feature selection and data quality.")
        
        if validation_results:
            cv_scores = validation_results.get("validation", {}).get("cross_val_scores", [])
            if cv_scores and np.std(cv_scores) > 0.1:
                recommendations.append("High variance in cross-validation scores. Model may be overfitting.")
        
        # Feature importance recommendations
        top_features = insights.get("top_features", [])
        if len(top_features) < 5:
            recommendations.append("Limited feature set detected. Consider adding more relevant features.")
        
        return recommendations

# Global model trainer instance
model_trainer = ModelTrainer()