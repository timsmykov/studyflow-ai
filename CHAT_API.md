# AI Chat API - StudyFlow

## Overview

The AI Chat API provides a ChatGPT-like streaming response system for the StudyFlow learning platform. It uses OpenAI's GPT-4o model with context management, token counting, and latency tracking.

## Features

- **Streaming Responses**: Server-Sent Events (SSE) for real-time AI responses
- **Context Management**: Maintains the last 20 messages in the conversation history
- **Adaptive Complexity**: Supports three response complexity levels (brief, standard, deep)
- **Token Counting**: Accurate token counting using tiktoken
- **Latency Tracking**: Measures response generation time
- **Course Context**: Includes course information in the system prompt
- **Clerk Authentication**: JWT-based authentication via Clerk

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Update your `.env` file with the following variables:

```env
# OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# Clerk Auth
CLERK_JWT_ISSUER=https://your-clerk-instance.clerk.accounts.dev
CLERK_JWT_PUBLIC_KEY_URL=https://your-clerk-instance.clerk.accounts.dev/.well-known/jwks.json

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/studyflow

# CORS
FRONTEND_URL=http://localhost:3000
```

## Running the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST /chat/

Send a chat message and receive a streaming AI response.

**Authentication:** Required (Clerk JWT in Authorization header)

**Request Body:**
```json
{
  "session_id": 1,          // Optional: Existing session ID
  "content": "Explain photosynthesis",
  "course_id": "BIO101",     // Course identifier for context
  "complexity": "standard"   // Optional: "brief", "standard", or "deep"
}
```

**Response:** Server-Sent Events (SSE) stream

Each event contains a JSON object:
```json
{"content": "Text chunk"}
```

Final event:
```json
{"done": true}
```

Error event:
```json
{"error": true, "message": "Error description"}
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Authorization: Bearer <clerk_jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "content": "Explain the concept of photosynthesis",
    "course_id": "BIO101",
    "complexity": "standard"
  }'
```

**Example using JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/chat/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${clerkJwt}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    session_id: 1,
    content: 'Explain photosynthesis',
    course_id: 'BIO101',
    complexity: 'standard'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (data.content) {
        console.log(data.content); // Handle content chunk
      } else if (data.done) {
        console.log('Stream complete');
      } else if (data.error) {
        console.error('Error:', data.message);
      }
    }
  }
}
```

### GET /chat/sessions/{session_id}

Get information about a specific chat session and its messages.

**Authentication:** Required

**Response:**
```json
{
  "session": {
    "id": 1,
    "course_id": "BIO101",
    "created_at": "2024-01-15T10:30:00"
  },
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Explain photosynthesis",
      "tokens": 5,
      "latency_ms": 0,
      "created_at": "2024-01-15T10:30:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Photosynthesis is the process...",
      "tokens": 120,
      "latency_ms": 1500,
      "created_at": "2024-01-15T10:30:01"
    }
  ]
}
```

## Complexity Levels

The API supports three complexity levels that affect the AI's response style:

### Brief
- Concise, to-the-point answers
- Minimal explanation
- Best for quick fact-checking
- System prompt: "concise answers, keep explanations short and to the point"

### Standard (Default)
- Detailed explanations
- Clear and thorough answers
- Balanced approach
- System prompt: "detailed explanations, provide clear and thorough answers"

### Deep
- Extensive explanations with examples
- Includes analogies and in-depth analysis
- Best for learning complex concepts
- System prompt: "extensive explanations with examples, analogies, and in-depth analysis"

## System Prompt Template

The system prompt is dynamically generated based on the course and complexity:

```
You are an AI tutor for {course_name}.
Complexity: {complexity} ({complexity_description})
Help students understand concepts, guide them through problems, never give direct answers without explanation.
```

## Token Counting

The API uses `tiktoken` for accurate token counting:
- User messages: Tokens counted before saving to database
- Assistant messages: Tokens counted after generation
- Tokens are stored in the `tokens` field of the Message model

Fallback method (if tiktoken fails): Approximation using ~4 characters per token

## Latency Tracking

Response latency is measured for assistant messages:
- `latency_ms` field in the Message model
- Measures time from request start to completion of response generation
- Does not include network latency

## Context Window

The API maintains the last 20 messages in the conversation history:
- Includes both user and assistant messages
- Ordered by creation time
- Automatically pruned when exceeding the limit
- Used to provide context to the AI for better responses

## Error Handling

The API handles various error scenarios:
- Invalid authentication: 401 Unauthorized
- Invalid complexity level: 400 Bad Request
- Empty message content: 400 Bad Request
- OpenAI API errors: 500 Internal Server Error
- Database errors: 500 Internal Server Error

Errors are sent as SSE events with `error: true` flag.

## Database Schema

Messages are stored in the `messages` table with the following fields:
- `id`: Primary key
- `session_id`: Foreign key to sessions table
- `role`: 'user', 'assistant', or 'system'
- `content`: Message text (max 10,000 characters)
- `tokens`: Token count
- `latency_ms`: Latency in milliseconds (for assistant messages)
- `created_at`: Timestamp

## Testing

Run the test suite:

```bash
pytest tests/test_chat.py
```

## License

MIT License
