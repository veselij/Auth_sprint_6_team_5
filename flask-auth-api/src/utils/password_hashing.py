import string
from secrets import choice as secrets_choice

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def generate_random_string():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets_choice(alphabet) for _ in range(16))
