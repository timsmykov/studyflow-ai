from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from app.models import Student, BKTProgressUpdate, BKTProgressRead
from app.database import get_db
from app.services.bkt_service import bkt_service
from app.utils.clerk_auth import get_current_clerk_user

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("/skills/{skill_id}", response_model=BKTProgressRead)
async def update_skill_progress(
    skill_id: str,
    update_data: BKTProgressUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Update a student's mastery for a specific skill using BKT.

    Args:
        skill_id: The skill identifier (e.g., "math:algebra:variables")
        update_data: {correct: bool} - Whether the student answered correctly

    Returns updated mastery (0-1 scale).
    """
    clerk_id = current_user["user_id"]

    # Get student
    student = db.query(Student).filter(Student.clerk_id == clerk_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    # Update progress using BKT
    progress = bkt_service.update_progress(
        db=db,
        student_id=student.id,
        skill_id=skill_id,
        correct=update_data.correct
    )

    return progress


@router.get("/skills/{skill_id}", response_model=BKTProgressRead)
async def get_skill_progress(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Get a student's mastery for a specific skill.
    """
    clerk_id = current_user["user_id"]

    # Get student
    student = db.query(Student).filter(Student.clerk_id == clerk_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    # Get progress
    from app.models import BKTProgress
    progress = db.query(BKTProgress).filter(
        BKTProgress.student_id == student.id,
        BKTProgress.skill_id == skill_id
    ).first()

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress data found for this skill"
        )

    return progress


@router.get("/skills", response_model=List[BKTProgressRead])
async def get_all_skills_progress(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Get all skill mastery progress for the current student.
    """
    clerk_id = current_user["user_id"]

    # Get student
    student = db.query(Student).filter(Student.clerk_id == clerk_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    # Get all progress
    progress_list = bkt_service.get_all_student_skills(db, student.id)

    return progress_list
