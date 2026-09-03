from pydantic import BaseModel,EmailStr,Field
#Validate incoming data
class RegisterRequest(BaseModel):
    email : EmailStr 
    password : str = Field(min_length=8 , max_length=128)
class LoginRequest(BaseModel):
    email : EmailStr
    password : str = Field(min_length=8, max_length=128)
class AuthResponse(BaseModel):
    #Standard response return after authencation.
    message : str