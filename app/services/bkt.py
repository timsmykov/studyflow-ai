"""
Bayesian Knowledge Tracing (BKT) Service

Implements the BKT model for tracking student skill mastery.
Formula:
P(L_n) = P(L_{n-1}) + (1 - P(L_{n-1})) * P(T)

Where:
- P(L_0): Initial mastery probability (default 0.5)
- P(T): Probability of transitioning from not-known to known
- P(G): Guess probability (probability of correct answer if not mastered)
- P(S): Slip probability (probability of incorrect answer if mastered)
"""

from typing import Optional
from datetime import datetime
from app.models import BKTProgress
from sqlalchemy.orm import Session


class BKTModel:
    """Bayesian Knowledge Tracing Model"""

    def __init__(
        self,
        p_initial: float = 0.5,
        p_learn: float = 0.3,
        p_guess: float = 0.2,
        p_slip: float = 0.1,
        mastery_threshold: float = 0.95
    ):
        """
        Initialize BKT model parameters.

        Args:
            p_initial: Initial mastery probability (default: 0.5)
            p_learn: Transition probability (default: 0.3)
            p_guess: Guess probability (default: 0.2)
            p_slip: Slip probability (default: 0.1)
            mastery_threshold: Threshold to consider skill mastered (default: 0.95)
        """
        self.p_initial = p_initial
        self.p_learn = p_learn
        self.p_guess = p_guess
        self.p_slip = p_slip
        self.mastery_threshold = mastery_threshold

    def update_mastery(self, current_mastery: float, is_correct: bool) -> float:
        """
        Update mastery probability based on student response.

        Args:
            current_mastery: Current mastery probability (0-1)
            is_correct: Whether the student answered correctly

        Returns:
            Updated mastery probability (0-1)
        """
        # Update mastery based on observation
        if is_correct:
            # Correct answer: increased probability of mastery
            numerator = current_mastery * (1 - self.p_slip)
            denominator = numerator + (1 - current_mastery) * self.p_guess
            p_l_given_correct = numerator / denominator if denominator > 0 else current_mastery

            # Apply learning transition
            new_mastery = p_l_given_correct + (1 - p_l_given_correct) * self.p_learn
        else:
            # Incorrect answer: decreased probability of mastery
            numerator = current_mastery * self.p_slip
            denominator = numerator + (1 - current_mastery) * (1 - self.p_guess)
            p_l_given_incorrect = numerator / denominator if denominator > 0 else current_mastery

            # Apply learning transition (can still learn from mistakes)
            new_mastery = p_l_given_incorrect + (1 - p_l_given_incorrect) * self.p_learn

        # Clamp to valid range
        return max(0.0, min(1.0, new_mastery))

    def is_mastered(self, mastery: float) -> bool:
        """Check if skill is considered mastered."""
        return mastery >= self.mastery_threshold


# Default BKT model instance
default_bkt = BKTModel()


def get_or_create_progress(
    session: Session,
    student_id: int,
    skill_id: str,
    bkt_model: Optional[BKTModel] = None
) -> BKTProgress:
    """
    Get or create BKT progress record for a student-skill pair.

    Args:
        session: Database session
        student_id: Student ID
        skill_id: Skill ID
        bkt_model: BKT model instance (uses default if not provided)

    Returns:
        BKTProgress record
    """
    model = bkt_model or default_bkt

    # Try to get existing progress
    progress = session.query(BKTProgress).filter(
        BKTProgress.student_id == student_id,
        BKTProgress.skill_id == skill_id
    ).first()

    if progress is None:
        # Create new progress with initial mastery
        progress = BKTProgress(
            student_id=student_id,
            skill_id=skill_id,
            mastery=model.p_initial,
            num_correct=0,
            num_incorrect=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(progress)
        session.commit()
        session.refresh(progress)

    return progress


def update_progress(
    session: Session,
    student_id: int,
    skill_id: str,
    is_correct: bool,
    bkt_model: Optional[BKTModel] = None
) -> BKTProgress:
    """
    Update BKT progress after a student response.

    Args:
        session: Database session
        student_id: Student ID
        skill_id: Skill ID
        is_correct: Whether the student answered correctly
        bkt_model: BKT model instance (uses default if not provided)

    Returns:
        Updated BKTProgress record
    """
    model = bkt_model or default_bkt

    # Get or create progress
    progress = get_or_create_progress(session, student_id, skill_id, model)

    # Update mastery using BKT model
    new_mastery = model.update_mastery(progress.mastery, is_correct)

    # Update counters
    if is_correct:
        progress.num_correct += 1
    else:
        progress.num_incorrect += 1

    # Update mastery and timestamp
    progress.mastery = new_mastery
    progress.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(progress)

    return progress


def get_student_skills(
    session: Session,
    student_id: int
) -> list[BKTProgress]:
    """
    Get all skills and their mastery for a student.

    Args:
        session: Database session
        student_id: Student ID

    Returns:
        List of BKTProgress records
    """
    return session.query(BKTProgress).filter(
        BKTProgress.student_id == student_id
    ).all()
