"""
Analytics API Endpoints

Endpoints for dropout prediction and student analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.database import get_session
from app.models import Student, DropoutPrediction, DropoutPredictionRead
from app.services.dropout import (
    predict_dropout_risk,
    predict_dropout_risk_with_explanation,
    init_predictor,
    predictor
)

router = APIRouter(tags=["analytics"])


# Initialize predictor on module load
@router.on_event("startup")
async def startup_event():
    """Initialize the dropout predictor on startup."""
    init_predictor(n_samples=500)


@router.get("/students/{student_id}/dropout-risk")
async def get_dropout_risk(
    student_id: int,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get dropout risk score for a specific student.

    Args:
        student_id: Student ID
        session: Database session

    Returns:
        Dictionary with risk score and details
    """
    # Verify student exists
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )

    # Extract features from student activity (mock data for now)
    features = _extract_student_features(student, session)

    # Predict dropout risk
    risk_score = predict_dropout_risk(features)

    # Get detailed prediction with feature importance
    detailed = predict_dropout_risk_with_explanation(features)

    # Save prediction to database
    prediction = DropoutPrediction(
        student_id=student_id,
        risk_score=risk_score / 100,  # Convert to 0-1 for storage
        features=features,
        predicted_at=datetime.utcnow()
    )
    session.add(prediction)
    session.commit()

    return {
        'student_id': student_id,
        'risk_score': round(risk_score, 2),
        'risk_level': _get_risk_level(risk_score),
        'features': features,
        'feature_importance': detailed['feature_importance'],
        'predicted_at': prediction.predicted_at.isoformat()
    }


@router.get("/analytics/students")
async def get_all_students_with_risk(
    min_risk: float = 0.0,
    limit: int = 100,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get list of all students with their dropout risk scores.

    Args:
        min_risk: Minimum risk score to filter (0-100)
        limit: Maximum number of students to return
        session: Database session

    Returns:
        Dictionary with student list and statistics
    """
    # Get all students
    students = session.exec(select(Student).limit(limit)).all()

    result = []
    for student in students:
        # Get latest prediction
        prediction = session.exec(
            select(DropoutPrediction)
            .where(DropoutPrediction.student_id == student.id)
            .order_by(DropoutPrediction.predicted_at.desc())
            .limit(1)
        ).first()

        if prediction:
            risk_score = prediction.risk_score * 100
        else:
            # Generate new prediction if none exists
            features = _extract_student_features(student, session)
            risk_score = predict_dropout_risk(features)

            # Save new prediction
            prediction = DropoutPrediction(
                student_id=student.id,
                risk_score=risk_score / 100,
                features=features,
                predicted_at=datetime.utcnow()
            )
            session.add(prediction)

        # Only include if above minimum risk
        if risk_score >= min_risk:
            result.append({
                'student_id': student.id,
                'clerk_id': student.clerk_id,
                'risk_score': round(risk_score, 2),
                'risk_level': _get_risk_level(risk_score),
                'last_active': student.last_active.isoformat() if student.last_active else None,
                'predicted_at': prediction.predicted_at.isoformat()
            })

    session.commit()

    # Calculate statistics
    if result:
        risk_scores = [r['risk_score'] for r in result]
        stats = {
            'total_students': len(result),
            'avg_risk': round(sum(risk_scores) / len(risk_scores), 2),
            'high_risk_count': sum(1 for r in result if r['risk_level'] == 'high'),
            'medium_risk_count': sum(1 for r in result if r['risk_level'] == 'medium'),
            'low_risk_count': sum(1 for r in result if r['risk_level'] == 'low')
        }
    else:
        stats = {
            'total_students': 0,
            'avg_risk': 0.0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0
        }

    return {
        'students': result,
        'statistics': stats
    }


def _extract_student_features(student: Student, session: Session) -> Dict[str, float]:
    """
    Extract features from student activity for dropout prediction.

    Note: This is a mock implementation. In a real system, this would
    query actual activity data from various sources (logs, LMS, etc.).

    Args:
        student: Student object
        session: Database session

    Returns:
        Dictionary of feature values
    """
    # Mock features - in production, these would come from actual data
    import random

    # Generate somewhat realistic features based on student activity
    last_active_days = (datetime.utcnow() - (student.last_active or datetime.utcnow())).days

    features = {
        'logins_7d': random.randint(0, 10) if last_active_days < 7 else 0,
        'days_since_login': last_active_days,
        'videos_completed_7d': random.randint(0, 5) if last_active_days < 7 else 0,
        'assignments_submitted_7d': random.randint(0, 3) if last_active_days < 7 else 0,
        'quiz_avg_score': random.uniform(40, 100),
        'forum_posts_7d': random.randint(0, 3) if last_active_days < 7 else 0,
        'course_completion_pct': random.uniform(0, 100),
        'activity_streak': random.randint(0, 10) if last_active_days < 7 else 0
    }

    return features


def _get_risk_level(risk_score: float) -> str:
    """
    Get risk level category based on risk score.

    Args:
        risk_score: Risk score (0-100)

    Returns:
        Risk level: 'low', 'medium', or 'high'
    """
    if risk_score >= 70:
        return 'high'
    elif risk_score >= 40:
        return 'medium'
    else:
        return 'low'
