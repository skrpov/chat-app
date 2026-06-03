from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(settings.FERNET_KEY.encode())
    return _fernet


def encrypt(text: str) -> str:
    return _get_fernet().encrypt(text.encode()).decode()


def decrypt(text: str) -> str:
    try:
        return _get_fernet().decrypt(text.encode()).decode()
    except InvalidToken:
        return text
