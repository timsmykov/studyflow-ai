from typing import Optional
from datetime import datetime
from app.models import BKTProgress
from app.database import Session


class BKTService:
    """
    Bayesian Knowledge Tracing (BKT) implementation for skill mastery tracking.

    BKT models a skill as a hidden binary state (mastered/not mastered).
    The posterior probability of mastery is updated based on performance.
    """

    def __init__(self, l0: float = 0.2, t: float = 0.15, g: float = 0.1, s: float = 0.15):
        """
        Initialize BKT parameters.

        Args:
            l0 (float): Initial probability of knowing the skill (p(L0)), default 0.2
            t (float): Probability of transition from not knowing to knowing (p(T)), default 0.15
            g (float): Probability of guessing correctly without knowing (p(G)), default 0.1
            s (float): Probability of slip (error despite knowing) (p(S)), default 0.15
        """
        self.l0 = l0
        self.t = t
        self.g = g
        self.s = s

    def update_mastery(
        self,
        current_mastery: float,
        correct: bool
    ) -> float:
        """
        Update mastery probability based on observed outcome.

        Args:
            current_mastery (float): Current mastery probability (0-1)
            correct (bool): Whether the student answered correctly

        Returns:
            float: Updated mastery probability
        """
        if correct:
            # P(Lt | correct) = P(correct | Lt) * P(Lt) / P(correct)
            numerator = (1 - self.s) * current_mastery + self.g * (1 - current_mastery)
            denominator = (1 - self.s) * current_mastery + self.g * (1 - current_mastery)
            new_mastery = numerator / denominator if denominator > 0 else current_mastery

            # Apply transition: if not mastered, chance to become mastered
            new_mastery = new_mastery + self.t * (1 - new_mastery)

        else:
            # P(Lt | incorrect) = P(incorrect | Lt) * P(Lt) / P(incorrect)
            numerator = self.s * current_mastery + (1 - self.g) * (1 - current_mastery)
            denominator = self.s * current_mastery + (1 - self.g) * (1 - current_mastery)
            new_mastery = numerator / denominator if denominator > 0 else current_mastery

            # Apply transition
            new_mastery = new_mastery + self.t * (1 - new_mastery)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, new_mastery))

    def get_or_create_progress(
        self,
        db: Session,
        student_id: int,
        skill_id: str
    ) -> BKTProgress:
        """
        Get existing BKT progress or create new with default parameters.

        Args:
            db: Database session
            student_id: Student ID
            skill_id: Skill identifier

        Returns:
            BKTProgress: The progress record
        """
        progress = db.query(BKTProgress).filter(
            BKTProgress.student_id == student_id,
            BKTProgress.skill_id == skill_id
        ).first()

        if not progress:
            progress = BKTProgress(
                student_id=student_id,
                skill_id=skill_id,
                mastery=self.l0,  # Start with initial mastery
                num_correct=0,
                num_incorrect=0
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)

        return progress

    def update_progress(
        self,
        db: Session,
        student_id: int,
        skill_id: str,
        correct: bool
    ) -> BKTProgress:
        """
        Update student's mastery for a skill based on performance.

        Args:
            db: Database session
            student_id: Student ID
            skill_id: Skill identifier
            correct: Whether the student answered correctly

        Returns:
            BKTProgress: Updated progress record
        """
        progress = self.get_or_create_progress(db, student_id, skill_id)

        # Update mastery using BKT
        new_mastery = self.update_mastery(progress.mastery, correct)

        # Update counts
        if correct:
            progress.num_correct += 1
        else:
            progress.num_incorrect += 1

        progress.mastery = new_mastery
        progress.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(progress)

        return progress

    def get_all_student_skills(
        self,
        db: Session,
        student_id: int
    ) -> list[BKTProgress]:
        """Get all skill progress for a student."""
        return db.query(BKTProgress).filter(
            BKTProgress.student_id == student_id
        ).all()


# Global BKT service instance
bkt_service = BKTService()
