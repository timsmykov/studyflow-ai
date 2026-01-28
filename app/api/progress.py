"""
Progress API Endpoints

Endpoints for tracking student skill mastery using BKT (Bayesian Knowledge Tracing).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models import Student, BKTProgress, BKTProgressRead
from app.services.bkt import update_progress, get_student_skills, default_bkt

router = APIRouter(prefix="/students", tags=["progress"])


@router.post("/{student_id}/skills/{skill_id}/correct", response_model=BKTProgressRead)
async def record_correct_answer(
    student_id: int,
    skill_id: str,
    session: Session = Depends(get_session)
) -> BKTProgress:
    """
    Record a correct answer and update skill mastery.

    Args:
        student_id: Student ID
        skill_id: Skill ID
        session: Database session

    Returns:
        Updated BKTProgress record
    """
    # Verify student exists
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )

    # Update progress for correct answer
    try:
        progress = update_progress(
            session=session,
            student_id=student_id,
            skill_id=skill_id,
            is_correct=True,
            bkt_model=default_bkt
        )
        return progress
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update progress: {str(e)}"
        )


@router.post("/{student_id}/skills/{skill_id}/incorrect", response_model=BKTProgressRead)
async def record_incorrect_answer(
    student_id: int,
    skill_id: str,
    session: Session = Depends(get_session)
) -> BKTProgress:
    """
    Record an incorrect answer and update skill mastery.

    Args:
        student_id: Student ID
        skill_id: Skill ID
        session: Database session

    Returns:
        Updated BKTProgress record
    """
    # Verify student exists
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )

    # Update progress for incorrect answer
    try:
        progress = update_progress(
            session=session,
            student_id=student_id,
            skill_id=skill_id,
            is_correct=False,
            bkt_model=default_bkt
        )
        return progress
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update progress: {str(e)}"
        )


@router.get("/{student_id}/skills", response_model=List[BKTProgressRead])
async def get_student_skill_list(
    student_id: int,
    session: Session = Depends(get_session)
) -> List[BKTProgress]:
    """
    Get all skills and their mastery for a student.

    Args:
        student_id: Student ID
        session: Database session

    Returns:
        List of BKTProgress records
    """
    # Verify student exists
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found"
        )

    try:
        skills = get_student_skills(session, student_id)
        return skills
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch skills: {str(e)}"
        )
