"""
Tests for Dropout Prediction service.
"""

import pytest
import numpy as np
from app.services.dropout import DropoutPredictor, predictor


def test_predictor_initialization():
    """Test dropout predictor initialization."""
    pred = DropoutPredictor()
    assert pred.model is not None
    assert pred.is_trained is False
    assert len(pred.feature_names) == 8


def test_predictor_initialization_custom_params():
    """Test dropout predictor with custom parameters."""
    pred = DropoutPredictor(n_estimators=50, random_state=123)
    assert pred.model is not None
    assert pred.is_trained is False


def test_generate_mock_data():
    """Test mock data generation."""
    pred = DropoutPredictor()
    X, y = pred.generate_mock_data(n_samples=100)

    assert X.shape == (100, 8)  # 8 features
    assert y.shape == (100,)
    assert all(label in [0, 1] for label in y)


def test_train_model():
    """Test model training."""
    pred = DropoutPredictor()
    metrics = pred.train(n_samples=500)

    assert pred.is_trained is True
    assert 'accuracy' in metrics
    assert 'n_train_samples' in metrics
    assert 'n_test_samples' in metrics
    assert metrics['accuracy'] > 0


def test_predict_risk():
    """Test dropout risk prediction."""
    pred = DropoutPredictor()
    pred.train(n_samples=100)

    features = {
        'logins_7d': 5,
        'days_since_login': 1,
        'videos_completed_7d': 3,
        'assignments_submitted_7d': 2,
        'quiz_avg_score': 85.0,
        'forum_posts_7d': 2,
        'course_completion_pct': 75.0,
        'activity_streak': 7
    }

    risk = pred.predict(features)
    assert 0 <= risk <= 100


def test_predict_high_risk():
    """Test prediction for high-risk student."""
    pred = DropoutPredictor()
    pred.train(n_samples=100)

    # Low activity features
    features = {
        'logins_7d': 0,
        'days_since_login': 14,
        'videos_completed_7d': 0,
        'assignments_submitted_7d': 0,
        'quiz_avg_score': 45.0,
        'forum_posts_7d': 0,
        'course_completion_pct': 10.0,
        'activity_streak': 0
    }

    risk = pred.predict(features)
    assert 0 <= risk <= 100


def test_predict_low_risk():
    """Test prediction for low-risk student."""
    pred = DropoutPredictor()
    pred.train(n_samples=100)

    # High activity features
    features = {
        'logins_7d': 7,
        'days_since_login': 0,
        'videos_completed_7d': 5,
        'assignments_submitted_7d': 3,
        'quiz_avg_score': 92.0,
        'forum_posts_7d': 3,
        'course_completion_pct': 85.0,
        'activity_streak': 10
    }

    risk = pred.predict(features)
    assert 0 <= risk <= 100


def test_predict_with_explanation():
    """Test prediction with feature importance explanation."""
    pred = DropoutPredictor()
    pred.train(n_samples=100)

    features = {
        'logins_7d': 3,
        'days_since_login': 2,
        'videos_completed_7d': 2,
        'assignments_submitted_7d': 1,
        'quiz_avg_score': 75.0,
        'forum_posts_7d': 1,
        'course_completion_pct': 50.0,
        'activity_streak': 5
    }

    result = pred.predict_with_explanation(features)

    assert 'risk_score' in result
    assert 'feature_importance' in result
    assert 'features' in result
    assert 0 <= result['risk_score'] <= 100
    assert len(result['feature_importance']) == 8


def test_feature_importance():
    """Test feature importance is available."""
    pred = DropoutPredictor()
    pred.train(n_samples=100)

    importance = pred.model.feature_importances_

    assert len(importance) == 8
    assert all(0 <= imp <= 1 for imp in importance)
    assert abs(sum(importance) - 1.0) < 0.01  # Should sum to approximately 1


def test_predict_without_training():
    """Test that prediction fails without training."""
    pred = DropoutPredictor()

    features = {
        'logins_7d': 5,
        'days_since_login': 1,
        'videos_completed_7d': 3,
        'assignments_submitted_7d': 2,
        'quiz_avg_score': 85.0,
        'forum_posts_7d': 2,
        'course_completion_pct': 75.0,
        'activity_streak': 7
    }

    with pytest.raises(RuntimeError, match="Model must be trained"):
        pred.predict(features)
