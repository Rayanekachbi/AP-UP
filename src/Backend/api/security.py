# src/Backend/api/security.py

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie le mot de passe (en clair pour le développement)."""
    return plain_password == hashed_password

def hash_password(password: str) -> str:
    """Simule le hachage d'un mot de passe."""
    return password

def password_needs_hash(password: str) -> bool:
    """Indique si le mot de passe doit être re-haché."""
    return False