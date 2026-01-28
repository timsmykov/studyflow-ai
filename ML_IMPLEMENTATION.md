# StudyFlow ML Models Implementation

## Overview

Implementation of ML models for StudyFlow learning platform, including Bayesian Knowledge Tracing (BKT) for skill mastery tracking and Random Forest for dropout risk prediction.

---

## 1. BKT Service (Bayesian Knowledge Tracing)

**File:** `app/services/bkt.py`

### Model Parameters
- **P(L₀)**: Initial mastery probability (default: 0.5)
- **P(T)**: Transition probability - learn from not-known to known (default: 0.3)
- **P(G)**: Guess probability - correct answer without mastery (default: 0.2)
- **P(S)**: Slip probability - incorrect answer despite mastery (default: 0.1)
- **Mastery Threshold**: 0.95 (skill is considered mastered above this)

### Key Functions
```python
class BKTModel:
    - update_mastery(current_mastery, is_correct) -> float
    - is_mastered(mastery) -> bool

def get_or_create_progress(session, student_id, skill_id) -> BKTProgress
def update_progress(session, student_id, skill_id, is_correct) -> BKTProgress
def get_student_skills(session, student_id) -> List[BKTProgress]
```

### BKT Update Formula
For correct answer:
```
P(L|correct) = P(L) * (1 - P(S)) / [P(L) * (1 - P(S)) + (1 - P(L)) * P(G)]
P(L_new) = P(L|correct) + (1 - P(L|correct)) * P(T)
```

For incorrect answer:
```
P(L|incorrect) = P(L) * P(S) / [P(L) * P(S) + (1 - P(L)) * (1 - P(G))]
P(L_new) = P(L|incorrect) + (1 - P(L|incorrect)) * P(T)
```

---

## 2. Progress API

**File:** `app/api/progress.py`

### Endpoints

#### POST `/students/{student_id}/skills/{skill_id}/correct`
- Records a correct answer
- Updates skill mastery using BKT model
- Increments correct answer counter

#### POST `/students/{student_id}/skills/{skill_id}/incorrect`
- Records an incorrect answer
- Updates skill mastery using BKT model
- Increments incorrect answer counter

#### GET `/students/{student_id}/skills`
- Returns all skills and their mastery for a student
- Includes: skill_id, mastery level, correct/incorrect counts, timestamps

---

## 3. Dropout Prediction Service

**File:** `app/services/dropout.py`

### Model
- **Algorithm**: Random Forest Classifier
- **Estimators**: 100 trees
- **Max Depth**: 10
- **Min Samples Split**: 5

### 8 Core Features
1. `logins_7d` - Number of logins in last 7 days
2. `days_since_login` - Days since last login
3. `videos_completed_7d` - Videos completed in last 7 days
4. `assignments_submitted_7d` - Assignments submitted in last 7 days
5. `quiz_avg_score` - Average quiz score (0-100)
6. `forum_posts_7d` - Forum posts in last 7 days
7. `course_completion_pct` - Course completion percentage (0-100)
8. `activity_streak` - Consecutive days of activity

### Key Functions
```python
class DropoutPredictor:
    - generate_mock_data(n_samples) -> (X, y)
    - train(n_samples) -> Dict[metrics]
    - predict(features) -> float (0-100)
    - predict_with_explanation(features) -> Dict

def init_predictor(n_samples) -> Dict
def predict_dropout_risk(features) -> float
def predict_dropout_risk_with_explanation(features) -> Dict
```

### Risk Score Calculation
- **0-39**: Low risk
- **40-69**: Medium risk
- **70-100**: High risk

---

## 4. Analytics API

**File:** `app/api/analytics.py`

### Endpoints

#### GET `/students/{student_id}/dropout-risk`
- Returns dropout risk score (0-100)
- Includes risk level category
- Shows feature values and their importance
- Saves prediction to database

#### GET `/analytics/students`
- Returns list of all students with risk scores
- Optional filters: `min_risk`, `limit`
- Includes statistics:
  - Total students count
  - Average risk
  - High/medium/low risk counts

### Risk Level Classification
```python
def _get_risk_level(risk_score):
    - >= 70: high
    - >= 40: medium
    - < 40: low
```

---

## 5. Database Models

**File:** `app/models.py`

### BKTProgress
```python
- id: int (primary key)
- student_id: int (foreign key)
- skill_id: str
- mastery: float (0.0-1.0)
- num_correct: int
- num_incorrect: int
- created_at: datetime
- updated_at: datetime
```

### DropoutPrediction
```python
- id: int (primary key)
- student_id: int (foreign key)
- risk_score: float (0.0-1.0)
- features: dict (JSON)
- predicted_at: datetime
```

---

## 6. Tests

### BKT Tests (`tests/test_bkt.py`)
- Model initialization (default and custom parameters)
- Mastery update for correct/incorrect answers
- Consecutive answer patterns
- Mastery threshold detection
- Boundary value handling

### Dropout Tests (`tests/test_dropout.py`)
- Predictor initialization
- Mock data generation
- Model training
- Risk prediction (high/low risk scenarios)
- Prediction with feature importance
- Feature importance validation

---

## 7. File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application with routers
│   ├── config.py               # Configuration
│   ├── database.py             # Database session management
│   ├── models.py               # SQLModel definitions
│   ├── api/
│   │   ├── __init__.py
│   │   ├── progress.py         # BKT API endpoints
│   │   └── analytics.py        # Dropout prediction endpoints
│   └── services/
│       ├── __init__.py
│       ├── bkt.py              # BKT model implementation
│       └── dropout.py          # Dropout prediction model
├── tests/
│   ├── test_bkt.py             # BKT service tests
│   └── test_dropout.py         # Dropout service tests
├── requirements.txt            # Python dependencies
└── .gitignore
```

---

## 8. API Usage Examples

### Record Correct Answer
```bash
curl -X POST "http://localhost:8000/students/1/skills/algebra/correct"
```

### Get Student Skills
```bash
curl "http://localhost:8000/students/1/skills"
```

### Get Dropout Risk
```bash
curl "http://localhost:8000/students/1/dropout-risk"
```

### Get All Students with Risk
```bash
curl "http://localhost:8000/analytics/students?min_risk=50&limit=100"
```

---

## 9. Dependencies

All required dependencies are in `requirements.txt`:
- fastapi>=0.109.0
- sqlmodel>=0.0.14
- scikit-learn>=1.4.0
- numpy>=1.26.0
- scipy>=1.12.0
- pandas>=2.2.0
- pytest>=8.0.0

---

## 10. Setup & Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

---

## 11. Future Enhancements

### BKT Improvements
- Skill-specific parameter tuning
- Multi-skill interaction models
- Time-based mastery decay

### Dropout Prediction Enhancements
- Real-time feature extraction from activity logs
- Model retraining with production data
- Ensemble methods for improved accuracy
- Explainable AI (SHAP values)

### API Enhancements
- Pagination for student lists
- Filtering and sorting options
- Export functionality (CSV, JSON)
- Real-time WebSocket updates

---

## 12. Git Commit

**Commit:** 90088cb
**Message:** feat: implement ML models for StudyFlow (BKT + Dropout Prediction)

All changes have been committed to the repository in `/root/molt-agents/studyflow/backend`.
