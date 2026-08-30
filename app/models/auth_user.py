from sqlalchemy import Boolean, String, false
from sqlalchemy.orm import Mapped , mapped_column
from app.models.base import BaseModel
class AuthUser(BaseModel):
    # Stores authentication information.
    #Every user needs a unique ID.
    id : Mapped[int] = mapped_column(
        primary_key=True , 
        index= True,
    )
    #This is the login email
    email : Mapped[str] = mapped_column(
        String(255) , 
        unique=True,
        index=True,
        nullable=False
    )
    password_hash : Mapped[str] = mapped_column(
        String(255),nullable=False
    )
    is_active : Mapped[bool] = mapped_column(
        Boolean, default=True , nullable=False
    )
    is_email_verified : Mapped[bool] = mapped_column(
        Boolean , default=False , nullable=False
    )
    #If user is admin(superuser) or regular user
    is_superuser:Mapped[bool]=mapped_column(
        Boolean , default=False , nullable=False
    )