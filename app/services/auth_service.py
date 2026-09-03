from app.repositories.auth_repository import Auth_repository
from app.models.auth_user import AuthUser
from app.core.security import hash_passwords
from app.schemas.auth import RegisterRequest
class AuthService:

    def __init__(self, repository : Auth_repository):
        self.repository = repository
    def register_user(self , request : RegisterRequest)->AuthUser:
        existing_user = self.repository.get_by_email(request.email)
        if existing_user:
            raise ValueError("Email is already registerd")
        password_hash= hash_passwords(request.password)

        user=self.repository.create_user(
            email=request.email,
            password_hash=password_hash
        )
        return user
        
