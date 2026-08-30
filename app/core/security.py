from pwdlib import PasswordHash
password_hash=PasswordHash.recommended()
def hash_passwords(password : str)-> str:
    #convert plain password into secure hash.
    return password_hash.hash(password)
def verify_password(
    plain_password : str , 
    hashed_password : str) -> bool:
    #verify a password against its hash.
    return password_hash.verify(plain_password , hashed_password)