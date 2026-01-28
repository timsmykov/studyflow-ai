from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from app.models import Student, StudentCreate, StudentRead, Session as ChatSession, SessionCreate, SessionRead
from app.database import get_db
from app.utils.clerk_auth import get_current_clerk_user

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Create a new student record.

    The clerk_id is validated against the authenticated user's ID.
    """
    clerk_id = current_user["user_id"]

    # Verify the clerk_id matches
    if student_data.clerk_id != clerk_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create student for another user"
        )

    # Check if student already exists
    existing = db.query(Student).filter(Student.clerk_id == clerk_id).first()
    if existing:
        return existing

    student = Student(clerk_id=clerk_id)
    db.add(student)
    db.commit()
    db.refresh(student)

    return student


@router.get("/me", response_model=StudentRead)
async def get_current_student(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Get the current authenticated student's profile.
    """
    clerk_id = current_user["user_id"]
    student = db.query(Student).filter(Student.clerk_id == clerk_id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    return student


@router.get("/{student_id}", response_model=StudentRead)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Get a specific student by ID (admin/self access only).
    """
    clerk_id = current_user["user_id"]
    student = db.get(Student, student_id)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Verify ownership
    if student.clerk_id != clerk_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return student


@router.post("/{student_id}/sessions", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    student_id: int,
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Create a new chat session for a student.
    """
    clerk_id = current_user["user_id"]

    # Verify student exists and belongs to user
    student = db.get(Student, student_id)
    if not student or student.clerk_id != clerk_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or access denied"
        )

    session = ChatSession(
        student_id=student_id,
        course_id=session_data.course_id
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.get("/{student_id}/sessions", response_model=List[SessionRead])
async def get_student_sessions(
    student_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Get all chat sessions for a student.
    """
    clerk_id = current_user["user_id"]

    # Verify student exists and belongs to user
    student = db.get(Student, student_id)
    if not student or student.clerk_id != clerk_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or access denied"
        )

    sessions = db.query(ChatSession).filter(
        ChatSession.student_id == student_id
    ).offset(skip).limit(limit).all()

    return sessions
