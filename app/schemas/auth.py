from email import message

from pydantic import BaseModel,EmailStr,Field
#Validate incoming data
class RegisterRequest(BaseModel):
    Email : EmailStr 
    password : str = Field(min_length=8 , max_length=128)
class LoginRequest(BaseModel):
    Email : EmailStr
    password : str
class AuthResponse(BaseModel):
    #Standard response return after authencation.
    message : str