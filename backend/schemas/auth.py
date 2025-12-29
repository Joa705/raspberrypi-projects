from pydantic import BaseModel, Field

class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    is_admin: bool = Field(..., description="Indicates if the user has admin privileges")
