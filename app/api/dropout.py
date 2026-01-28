from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.models import Student, DropoutPredictionRead
from app.database import get_db
from app.services.dropout_service import dropout_service
from app.utils.clerk_auth import get_current_clerk_user

router = APIRouter(prefix="/dropout", tags=["dropout"])


@router.get("/risk", response_model=DropoutPredictionRead)
async def get_dropout_risk(
    force_refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Get the current student's dropout risk prediction.

    If force_refresh is True, generates a new prediction.
    Otherwise returns the most recent prediction (if less than 24h old).
    """
    clerk_id = current_user["user_id"]

    # Get student
    student = db.query(Student).filter(Student.clerk_id == clerk_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    # Generate new prediction or return cached
    if force_refresh:
        prediction = dropout_service.predict_and_save(db, student.id)
    else:
        prediction = dropout_service.get_latest_prediction(db, student.id)
        if not prediction:
            # No recent prediction, generate one
            prediction = dropout_service.predict_and_save(db, student.id)

    return prediction


@router.get("/features")
async def get_dropout_features(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Get the current student's engagement features without generating a prediction.

    Useful for debugging and understanding what factors influence the risk score.
    """
    clerk_id = current_user["user_id"]

    # Get student
    student = db.query(Student).filter(Student.clerk_id == clerk_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    # Extract features
    features = dropout_service.extract_features(db, student.id)

    return features


@router.get("/history", response_model=list[DropoutPredictionRead])
async def get_dropout_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user)
):
    """
    Get historical dropout predictions for the current student.
    """
    clerk_id = current_user["user_id"]

    # Get student
    student = db.query(Student).filter(Student.clerk_id == clerk_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    # Get prediction history
    from app.models import DropoutPrediction
    predictions = db.query(DropoutPrediction).filter(
        DropoutPrediction.student_id == student.id
    ).order_by(DropoutPrediction.predicted_at.desc()).limit(limit).all()

    return predictions
