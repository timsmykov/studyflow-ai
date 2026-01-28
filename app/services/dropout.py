"""
Dropout Prediction Service

Uses Random Forest to predict student dropout risk based on activity features.
Features:
1. Logins in last 7 days
2. Days since last login
3. Videos completed (last 7 days)
4. Assignments submitted (last 7 days)
5. Quiz average score
6. Forum posts (last 7 days)
7. Course completion percentage
8. Activity streak (consecutive days)
"""

import numpy as np
from typing import Dict, List, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import random


class DropoutPredictor:
    """Random Forest-based Dropout Risk Predictor"""

    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        """
        Initialize the dropout predictor.

        Args:
            n_estimators: Number of trees in the random forest
            random_state: Random seed for reproducibility
        """
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
            max_depth=10,
            min_samples_split=5
        )
        self.is_trained = False
        self.feature_names = [
            'logins_7d',
            'days_since_login',
            'videos_completed_7d',
            'assignments_submitted_7d',
            'quiz_avg_score',
            'forum_posts_7d',
            'course_completion_pct',
            'activity_streak'
        ]

    def generate_mock_data(self, n_samples: int = 500) -> tuple[np.ndarray, np.ndarray]:
        """
        Generate mock training data.

        Args:
            n_samples: Number of samples to generate

        Returns:
            Tuple of (features array, labels array)
        """
        np.random.seed(42)
        random.seed(42)

        features = []
        labels = []

        for _ in range(n_samples):
            # Generate realistic feature values
            logins_7d = np.random.poisson(3)  # Poisson distribution for login counts
            days_since_login = np.random.exponential(scale=2)  # More likely to have recent login
            videos_completed_7d = np.random.poisson(2)
            assignments_submitted_7d = np.random.poisson(1)
            quiz_avg_score = np.clip(np.random.normal(75, 15), 0, 100)  # Normal distribution
            forum_posts_7d = np.random.poisson(1)
            course_completion_pct = np.random.uniform(0, 100)
            activity_streak = np.random.poisson(3)

            feature_vector = [
                logins_7d,
                days_since_login,
                videos_completed_7d,
                assignments_submitted_7d,
                quiz_avg_score,
                forum_posts_7d,
                course_completion_pct,
                activity_streak
            ]

            # Determine dropout risk label based on features
            # High risk: low activity, low completion, long time since login
            risk_score = self._calculate_mock_risk(feature_vector)

            # Binary label: 1 = dropout risk, 0 = no risk
            label = 1 if risk_score > 0.5 else 0

            features.append(feature_vector)
            labels.append(label)

        return np.array(features), np.array(labels)

    def _calculate_mock_risk(self, features: List[float]) -> float:
        """Calculate mock risk score for label generation."""
        logins_7d, days_since_login, videos_completed_7d, assignments_submitted_7d, \
        quiz_avg_score, forum_posts_7d, course_completion_pct, activity_streak = features

        # Heuristic risk calculation
        risk = 0.0

        # Low logins increase risk
        risk += max(0, (5 - logins_7d) * 0.1)

        # Long time since login increases risk
        risk += min(0.3, days_since_login * 0.05)

        # Low videos increase risk
        risk += max(0, (3 - videos_completed_7d) * 0.05)

        # Low assignments increase risk
        risk += max(0, (2 - assignments_submitted_7d) * 0.08)

        # Low quiz scores increase risk
        risk += max(0, (70 - quiz_avg_score) * 0.005)

        # Low forum posts increase risk
        risk += max(0, (2 - forum_posts_7d) * 0.04)

        # Low completion increases risk
        risk += (100 - course_completion_pct) * 0.002

        # Low streak increases risk
        risk += max(0, (5 - activity_streak) * 0.03)

        return min(1.0, max(0.0, risk / 2.0))  # Normalize roughly

    def train(self, n_samples: int = 500) -> Dict:
        """
        Train the model on mock data.

        Args:
            n_samples: Number of training samples

        Returns:
            Training metrics dictionary
        """
        # Generate mock data
        X, y = self.generate_mock_data(n_samples)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        return {
            'accuracy': accuracy,
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test)
        }

    def predict(self, features: Dict[str, float]) -> float:
        """
        Predict dropout risk score (0-100).

        Args:
            features: Dictionary of feature values

        Returns:
            Risk score between 0 and 100
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        # Extract features in correct order
        feature_vector = [
            features.get('logins_7d', 0),
            features.get('days_since_login', 7),
            features.get('videos_completed_7d', 0),
            features.get('assignments_submitted_7d', 0),
            features.get('quiz_avg_score', 0),
            features.get('forum_posts_7d', 0),
            features.get('course_completion_pct', 0),
            features.get('activity_streak', 0)
        ]

        # Reshape for prediction
        X = np.array([feature_vector])

        # Get probability of dropout (class 1)
        prob = self.model.predict_proba(X)[0][1]

        # Convert to 0-100 scale
        return prob * 100

    def predict_with_explanation(
        self, features: Dict[str, float]
    ) -> Dict:
        """
        Predict dropout risk with feature importance explanation.

        Args:
            features: Dictionary of feature values

        Returns:
            Dictionary with risk score and feature contributions
        """
        risk_score = self.predict(features)

        # Get feature importance
        importance = dict(zip(self.feature_names, self.model.feature_importances_))

        return {
            'risk_score': risk_score,
            'feature_importance': importance,
            'features': features
        }


# Global predictor instance
predictor = DropoutPredictor()


def init_predictor(n_samples: int = 500) -> Dict:
    """
    Initialize and train the dropout predictor.

    Args:
        n_samples: Number of training samples

    Returns:
        Training metrics
    """
    if not predictor.is_trained:
        metrics = predictor.train(n_samples)
        return metrics
    return {'status': 'already_trained'}


def predict_dropout_risk(features: Dict[str, float]) -> float:
    """
    Predict dropout risk for a student.

    Args:
        features: Dictionary of student activity features

    Returns:
        Risk score between 0 and 100
    """
    return predictor.predict(features)


def predict_dropout_risk_with_explanation(features: Dict[str, float]) -> Dict:
    """
    Predict dropout risk with feature importance.

    Args:
        features: Dictionary of student activity features

    Returns:
        Dictionary with risk score and feature contributions
    """
    return predictor.predict_with_explanation(features)
