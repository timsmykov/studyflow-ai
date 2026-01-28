from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: Optional[int] = Field(default=None, primary_key=True)
    clerk_id: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = Field(default=None)

    # Relationships
    sessions: list["Session"] = Relationship(back_populates="student")
    bkt_progress: list["BKTProgress"] = Relationship(back_populates="student")
    dropout_predictions: list["DropoutPrediction"] = Relationship(back_populates="student")


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id", index=True)
    course_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    student: Student = Relationship(back_populates="sessions")
    messages: list["Message"] = Relationship(back_populates="session")


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    role: MessageRole = Field(index=True)
    content: str = Field(max_length=10000)
    tokens: Optional[int] = Field(default=0)
    latency_ms: Optional[int] = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    session: Session = Relationship(back_populates="messages")


class BKTProgress(SQLModel, table=True):
    __tablename__ = "bkt_progress"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id", index=True)
    skill_id: str = Field(index=True)
    mastery: float = Field(default=0.0, ge=0.0, le=1.0)
    num_correct: int = Field(default=0, ge=0)
    num_incorrect: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    student: Student = Relationship(back_populates="bkt_progress")


class DropoutPrediction(SQLModel, table=True):
    __tablename__ = "dropout_predictions"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id", index=True)
    risk_score: float = Field(ge=0.0, le=1.0)
    features: dict = Field(default={}, sa_column_kwargs={"type": "json"})
    predicted_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    student: Student = Relationship(back_populates="dropout_predictions")


# Pydantic models for API
class StudentCreate(SQLModel):
    clerk_id: str


class StudentRead(SQLModel):
    id: int
    clerk_id: str
    created_at: datetime
    last_active: Optional[datetime] = None


class SessionCreate(SQLModel):
    course_id: str


class SessionRead(SQLModel):
    id: int
    student_id: int
    course_id: str
    created_at: datetime


class MessageCreate(SQLModel):
    role: MessageRole
    content: str
    tokens: Optional[int] = None
    latency_ms: Optional[int] = None


class MessageRead(SQLModel):
    id: int
    session_id: int
    role: MessageRole
    content: str
    tokens: int
    latency_ms: int
    created_at: datetime


class BKTProgressUpdate(SQLModel):
    correct: bool


class BKTProgressRead(SQLModel):
    id: int
    student_id: int
    skill_id: str
    mastery: float
    num_correct: int
    num_incorrect: int
    updated_at: datetime


class DropoutPredictionRead(SQLModel):
    id: int
    student_id: int
    risk_score: float
    features: dict
    predicted_at: datetime


class ChatRequest(SQLModel):
    session_id: Optional[int] = None
    course_id: Optional[str] = None
    message: str
    stream: bool = True


class ChatResponse(SQLModel):
    session_id: int
    message_id: int
    content: str
    tokens: int
    latency_ms: int
