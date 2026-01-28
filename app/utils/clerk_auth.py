from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk
from jose.utils import base64url_decode
from typing import Dict, Any
import httpx
import json
from app.config import settings

security = HTTPBearer()


class ClerkAuthException(HTTPException):
    def __init__(self, detail: str = "Invalid authentication"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_clerk_public_keys() -> Dict[str, Dict[str, Any]]:
    """Fetch the public keys from Clerk JWKS endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(settings.CLERK_JWT_PUBLIC_KEY_URL)
        response.raise_for_status()
        jwks = response.json()
        return {key["kid"]: key for key in jwks["keys"]}


async def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify Clerk JWT token and return decoded claims."""
    try:
        token = credentials.credentials
        headers = jwt.get_unverified_headers(token)
        kid = headers.get("kid")

        if not kid:
            raise ClerkAuthException("Token missing key ID")

        public_keys = await get_clerk_public_keys()

        if kid not in public_keys:
            raise ClerkAuthException("Invalid token: unknown key ID")

        public_key = public_keys[kid]

        # Construct RSA public key from JWKS
        e = base64url_decode(public_key["e"])
        n = base64url_decode(public_key["n"])

        # Verify token
        payload = jwt.decode(
            token,
            key={
                "kty": public_key["kty"],
                "kid": kid,
                "use": public_key["use"],
                "e": e,
                "n": n,
            },
            algorithms=["RS256"],
            issuer=settings.CLERK_JWT_ISSUER,
            options={"verify_aud": False},
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise ClerkAuthException("Token expired")
    except jwt.JWTError as e:
        raise ClerkAuthException(f"Invalid token: {str(e)}")
    except Exception as e:
        raise ClerkAuthException(f"Authentication error: {str(e)}")


async def get_current_clerk_user(payload: Dict[str, Any] = Depends(verify_clerk_token)) -> Dict[str, Any]:
    """Extract current user information from verified token."""
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
    }
