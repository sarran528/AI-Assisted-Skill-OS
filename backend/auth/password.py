from passlib.context import CryptContext
import bcrypt
import re
import logging
from fastapi import HTTPException, status

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

def validate_password_strength(password: str) -> None:
    """
    Validates password strength according to security policy.
    Raises HTTPException if password doesn't meet requirements.
    """
    errors = []
    
    # Minimum length of 8 characters
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    # Maximum length of 72 characters (bcrypt limitation)
    if len(password) > 72:
        errors.append("Password cannot exceed 72 characters")
    
    # Must contain at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Must contain at least one lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Must contain at least one digit
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    # Must contain at least one special character
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]', password):
        errors.append("Password must contain at least one special character")
    
    # Check for common patterns
    if password.lower() in ['password', '12345678', 'qwerty123', 'admin123']:
        errors.append("Password is too common and easily guessable")
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Password validation failed", "errors": errors}
        )


def hash_password(password: str) -> str:
    validate_password_strength(password)
    # Truncate to 72 characters to comply with bcrypt limitations
    # Use bcrypt directly to avoid passlib context issues
    import bcrypt
    return bcrypt.hashpw(password[:72].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    try:
        # Truncate to 72 characters to comply with bcrypt limitations
        truncated_password = password[:72]
        logger.debug(f"Verifying password (len: {len(password)}, truncated: {len(truncated_password)})")
        
        # Use bcrypt directly to avoid passlib context issues
        import bcrypt
        result = bcrypt.checkpw(truncated_password.encode('utf-8'), hashed.encode('utf-8'))
        
        logger.debug(f"Password verification result: {result}")
        return result
        
    except ValueError as e:
        # Log the error and re-raise as HTTPException for better error handling
        logger.error(f"Password verification ValueError: {e}")
        # Instead of raising HTTPException, return False for invalid credentials
        return False
    except Exception as e:
        logger.error(f"Password verification unexpected error: {e}")
        # Return False for any other errors instead of raising exceptions
        return False
