from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.auth_user import AuthUser
class Auth_repository:
    def __init__(self , db:Session):
        self.db=db
    def get_by_email(self, email:str)->AuthUser|None:
        statement=select(AuthUser).where(AuthUser.email==email)
        result=self.db.execute(statement)
        result.scalar_one_or_none()
    def create_user(self,
                    *,
                    email:str,
                    password_hash:str
                    )->AuthUser|None:
        user=AuthUser(
            email=email,
            password_hash=password_hash
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    