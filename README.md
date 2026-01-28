# StudyFlow AI Backend

FastAPI-based backend for StudyFlow AI - an AI-powered learning platform with skill mastery tracking and dropout prediction.

## Features

- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Robust database with SQLModel ORM
- **Clerk Authentication** - JWT-based user authentication
- **OpenAI Integration** - GPT-4o chat with streaming support
- **Bayesian Knowledge Tracing (BKT)** - Skill mastery tracking
- **Dropout Prediction** - Random Forest model for student retention
- **RESTful API** - Clean, well-documented endpoints

## Project Structure

```
studyflow-backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Settings and configuration
│   ├── database.py             # Database connection and session management
│   ├── models.py               # SQLModel data models
│   ├── api/                    # API route handlers
│   │   ├── students.py         # Student endpoints
│   │   ├── chat.py             # Chat/OpenAI endpoints
│   │   ├── progress.py         # BKT progress endpoints
│   │   └── dropout.py          # Dropout prediction endpoints
│   ├── services/               # Business logic
│   │   ├── bkt_service.py      # Bayesian Knowledge Tracing
│   │   ├── dropout_service.py  # Dropout prediction (Random Forest)
│   │   └── chat_service.py     # OpenAI chat service
│   └── utils/                  # Helper utilities
│       └── clerk_auth.py       # Clerk JWT verification
├── tests/                      # Test suite
│   └── test_api.py             # API and service tests
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── railway.json               # Railway deployment config
└── README.md                  # This file
```

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Web framework
- **SQLModel** - ORM (Pydantic + SQLAlchemy)
- **PostgreSQL** - Database
- **Clerk** - Authentication
- **OpenAI** - GPT-4o API
- **scikit-learn** - Machine learning (Random Forest)
- **NumPy/SciPy** - Numerical computing

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Clerk account (for authentication)
- OpenAI API key

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd studyflow/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your values:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/studyflow
   CLERK_JWT_ISSUER=https://your-instance.clerk.accounts.dev
   CLERK_JWT_PUBLIC_KEY_URL=https://your-instance.clerk.accounts.dev/.well-known/jwks.json
   OPENAI_API_KEY=sk-your-openai-api-key
   OPENAI_MODEL=gpt-4o
   FRONTEND_URL=http://localhost:3000
   ENVIRONMENT=development
   LOG_LEVEL=info
   PORT=8000
   ```

5. **Set up PostgreSQL database**

   Create a database:
   ```bash
   createdb studyflow
   ```

   Or use Docker:
   ```bash
   docker run --name studyflow-db \
     -e POSTGRES_USER=studyflow \
     -e POSTGRES_PASSWORD=studyflow \
     -e POSTGRES_DB=studyflow \
     -p 5432:5432 \
     -d postgres:14-alpine
   ```

6. **Run the application**

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

7. **Access API documentation**

   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

All endpoints (except `/health` and `/`) require Clerk JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-clerk-jwt-token>
```

### Health Check

- **GET** `/health` - Health check endpoint
- **GET** `/` - Root endpoint with API info

### Students

- **POST** `/students` - Create a new student profile
- **GET** `/students/me` - Get current student profile
- **GET** `/students/{id}` - Get a specific student
- **POST** `/students/{id}/sessions` - Create a chat session
- **GET** `/students/{id}/sessions` - List student sessions

### Chat

- **POST** `/chat` - Send a message (non-streaming)
  ```json
  {
    "session_id": 123,
    "course_id": "math:algebra",
    "message": "What is a variable?",
    "stream": false
  }
  ```

- **POST** `/chat/stream` - Send a message (streaming)
  ```json
  {
    "session_id": null,
    "course_id": "math:algebra",
    "message": "Explain variables",
    "stream": true
  }
  ```

### Progress (BKT)

- **POST** `/progress/skills/{skill_id}` - Update skill mastery
  ```json
  {
    "correct": true
  }
  ```

- **GET** `/progress/skills/{skill_id}` - Get skill mastery
- **GET** `/progress/skills` - Get all skill progress

### Dropout Prediction

- **GET** `/dropout/risk` - Get dropout risk (cached or new)
- **GET** `/dropout/risk?force_refresh=true` - Force new prediction
- **GET** `/dropout/features` - Get engagement features
- **GET** `/dropout/history` - Get prediction history

## Services

### BKT Service (Bayesian Knowledge Tracking)

Tracks skill mastery using the BKT algorithm with parameters:
- **l0** (initial mastery): 0.2
- **t** (transition probability): 0.15
- **g** (guess probability): 0.1
- **s** (slip probability): 0.15

Mastery updates based on correct/incorrect answers.

### Dropout Service

Uses 8 core engagement features:
1. Session frequency (sessions/day)
2. Average messages per session
3. Days since last active
4. Average session length
5. Response latency
6. Average skill mastery
7. Correct answer rate
8. Active days (last 30 days)

Returns a risk score (0-1):
- **0.0 - 0.3**: Low risk
- **0.3 - 0.7**: Medium risk
- **0.7 - 1.0**: High risk

### Chat Service

Integrates with OpenAI GPT-4o:
- Supports both streaming and non-streaming responses
- Maintains session context
- Tracks tokens and latency
- Auto-creates sessions on demand

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app tests/
```

Run specific tests:

```bash
pytest tests/test_api.py::TestBKTService::test_bkt_update_correct
```

## Deployment

### Railway

1. **Create a Railway account** at [railway.app](https://railway.app)

2. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

3. **Login to Railway**
   ```bash
   railway login
   ```

4. **Initialize the project**
   ```bash
   railway init
   railway up
   ```

5. **Add environment variables**
   ```bash
   railway variables set DATABASE_URL=$DATABASE_URL
   railway variables set CLERK_JWT_ISSUER=$CLERK_JWT_ISSUER
   railway variables set CLERK_JWT_PUBLIC_KEY_URL=$CLERK_JWT_PUBLIC_KEY_URL
   railway variables set OPENAI_API_KEY=$OPENAI_API_KEY
   railway variables set FRONTEND_URL=https://your-frontend-url.railway.app
   railway variables set ENVIRONMENT=production
   railway variables set LOG_LEVEL=info
   ```

6. **Add PostgreSQL database**
   ```bash
   railway add postgresql
   ```

7. **Deploy**
   ```bash
   railway deploy
   ```

The application will be deployed with automatic HTTPS and health checks.

### Environment Variables for Production

- `DATABASE_URL` - PostgreSQL connection string (Railway auto-provides)
- `CLERK_JWT_ISSUER` - Your Clerk instance URL
- `CLERK_JWT_PUBLIC_KEY_URL` - JWKS endpoint from Clerk
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_MODEL` - Model to use (default: gpt-4o)
- `FRONTEND_URL` - Your frontend URL for CORS
- `ENVIRONMENT` - Set to "production"
- `PORT` - Railway auto-provides (default: 8000)

## Development Tips

### Database Migrations (Future)

For production, consider using Alembic for migrations:

```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Monitoring

- Check logs: `railway logs`
- View metrics in Railway dashboard
- Monitor PostgreSQL performance

### Performance

- Enable connection pooling in production
- Consider Redis for caching (future)
- Optimize database queries with indexes

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Test connection
psql postgresql://user:password@localhost:5432/studyflow
```

### Authentication Issues

- Verify Clerk JWT issuer URL
- Check JWKS endpoint is accessible
- Ensure token is not expired

### OpenAI API Errors

- Verify API key is valid
- Check API quota limits
- Ensure model is available

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Email: support@studyflow.ai

## Roadmap

- [ ] Add Redis caching
- [ ] Implement WebSocket for real-time updates
- [ ] Add more ML models for personalization
- [ ] Implement analytics dashboard
- [ ] Add rate limiting
- [ ] Implement database migrations with Alembic
