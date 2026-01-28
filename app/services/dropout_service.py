from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.models import Student, Session, Message, DropoutPrediction
from app.database import Session
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import json


class DropoutPredictionService:
    """
    Dropout prediction service using Random Forest classifier.

    Uses 8 core engagement signals to predict student dropout risk.
    """

    def __init__(self):
        # Initialize Random Forest model
        # In production, you'd load a pre-trained model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.model_trained = False

    def extract_features(
        self,
        db: Session,
        student_id: int,
        days_lookback: int = 30
    ) -> Dict[str, float]:
        """
        Extract 8 core engagement features for a student.

        Args:
            db: Database session
            student_id: Student ID
            days_lookback: Number of days to look back for engagement data

        Returns:
            Dict[str, float]: Feature dictionary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_lookback)

        # Get student
        student = db.get(Student, student_id)
        if not student:
            return {}

        # 1. Session frequency (sessions per day in last 30 days)
        sessions = db.query(Session).filter(
            Session.student_id == student_id,
            Session.created_at >= cutoff_date
        ).all()
        session_frequency = len(sessions) / max(days_lookback, 1)

        # 2. Average messages per session
        total_messages = 0
        for session in sessions:
            msg_count = db.query(Message).filter(Message.session_id == session.id).count()
            total_messages += msg_count
        avg_messages_per_session = total_messages / max(len(sessions), 1)

        # 3. Days since last active
        days_since_last_active = 0
        if student.last_active:
            days_since_last_active = (datetime.utcnow() - student.last_active).days

        # 4. Average session length (messages)
        avg_session_length = avg_messages_per_session

        # 5. Response latency (average time to next message)
        # This is a simplified version - in production, track actual latencies
        recent_messages = db.query(Message).join(Session).filter(
            Session.student_id == student_id,
            Message.created_at >= cutoff_date
        ).order_by(Message.created_at).all()

        avg_latency_ms = 0
        if len(recent_messages) > 1:
            latencies = [m.latency_ms or 0 for m in recent_messages if m.latency_ms]
            avg_latency_ms = np.mean(latencies) if latencies else 0

        # 6. Skill mastery progress (average mastery across all skills)
        from app.models import BKTProgress
        skill_progress = db.query(BKTProgress).filter(
            BKTProgress.student_id == student_id
        ).all()

        avg_mastery = 0.0
        if skill_progress:
            avg_mastery = np.mean([p.mastery for p in skill_progress])

        # 7. Correct answer rate (across all skill attempts)
        total_correct = sum([p.num_correct for p in skill_progress])
        total_incorrect = sum([p.num_incorrect for p in skill_progress])
        total_attempts = total_correct + total_incorrect
        correct_rate = total_correct / max(total_attempts, 1)

        # 8. Active days (unique days with sessions in lookback period)
        session_dates = set([s.created_at.date() for s in sessions])
        active_days = len(session_dates)

        features = {
            "session_frequency": float(session_frequency),
            "avg_messages_per_session": float(avg_messages_per_session),
            "days_since_last_active": float(days_since_last_active),
            "avg_session_length": float(avg_session_length),
            "avg_latency_ms": float(avg_latency_ms),
            "avg_mastery": float(avg_mastery),
            "correct_rate": float(correct_rate),
            "active_days": float(active_days),
        }

        return features

    def predict_dropout_risk(
        self,
        features: Dict[str, float]
    ) -> float:
        """
        Predict dropout risk score (0-1).

        Args:
            features: Feature dictionary

        Returns:
            float: Risk score (0 = low risk, 1 = high risk)
        """
        # In production, this would use a trained model
        # For MVP, we'll use a heuristic approach

        # Higher risk factors:
        # - Low session frequency
        # - Few messages per session
        # - High days since last active
        # - High latency
        # - Low mastery
        # - Low correct rate
        # - Few active days

        risk_score = 0.0

        # Normalize and weigh each feature
        risk_score += max(0, 1.0 - features.get("session_frequency", 0)) * 0.15
        risk_score += max(0, 1.0 - features.get("avg_messages_per_session", 0) / 10) * 0.10
        risk_score += min(1.0, features.get("days_since_last_active", 0) / 14) * 0.20
        risk_score += max(0, 1.0 - features.get("avg_session_length", 0) / 5) * 0.10
        risk_score += min(1.0, features.get("avg_latency_ms", 0) / 10000) * 0.05
        risk_score += max(0, 1.0 - features.get("avg_mastery", 0)) * 0.15
        risk_score += max(0, 1.0 - features.get("correct_rate", 0)) * 0.15
        risk_score += max(0, 1.0 - features.get("active_days", 0) / 10) * 0.10

        # Clamp to [0, 1]
        return max(0.0, min(1.0, risk_score))

    def predict_and_save(
        self,
        db: Session,
        student_id: int
    ) -> DropoutPrediction:
        """
        Generate and save a dropout prediction for a student.

        Args:
            db: Database session
            student_id: Student ID

        Returns:
            DropoutPrediction: The prediction record
        """
        features = self.extract_features(db, student_id)
        risk_score = self.predict_dropout_risk(features)

        # Create prediction record
        prediction = DropoutPrediction(
            student_id=student_id,
            risk_score=risk_score,
            features=features,
            predicted_at=datetime.utcnow()
        )

        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        return prediction

    def get_latest_prediction(
        self,
        db: Session,
        student_id: int,
        max_age_hours: int = 24
    ) -> Optional[DropoutPrediction]:
        """
        Get the most recent dropout prediction for a student.

        Args:
            db: Database session
            student_id: Student ID
            max_age_hours: Maximum age of prediction in hours

        Returns:
            DropoutPrediction or None
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

        prediction = db.query(DropoutPrediction).filter(
            DropoutPrediction.student_id == student_id,
            DropoutPrediction.predicted_at >= cutoff
        ).order_by(DropoutPrediction.predicted_at.desc()).first()

        return prediction


# Global service instance
dropout_service = DropoutPredictionService()
