import bcrypt

# Function to hash password
def _prepare_password(pw: str) -> str:
    if pw is None:
        return ''
    s = str(pw)
    try:
        b = s.encode('utf-8')
    except Exception:
        b = s.encode('utf-8', errors='ignore')
    if len(b) > 72:
        import hashlib
        return hashlib.sha256(b).hexdigest()
    return s

def hash_password(password: str):
    # Prepare password to avoid bcrypt's 72-byte limit, then hash.
    s = _prepare_password(password).encode('utf-8')
    return bcrypt.hashpw(s, bcrypt.gensalt()).decode('utf-8')

def verify_password(
    plain_password: str,
    hashed_password: str
):
    if not hashed_password:
        return False

    s = _prepare_password(plain_password).encode('utf-8')
    hashed = hashed_password.encode('utf-8')

    if hashed_password.startswith(('$2a$', '$2b$', '$2y$')):
        return bcrypt.checkpw(s, hashed)

    # Legacy fallback for older passlib-generated hashes. Keep bcrypt out of
    # passlib here because bcrypt 5 raises during passlib's backend probe.
    try:
        from passlib.context import CryptContext

        if hashed_password.startswith("$pbkdf2-sha256$"):
            pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        elif hashed_password.startswith("$bcrypt-sha256$"):
            pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
        else:
            return False
        return pwd_context.verify(_prepare_password(plain_password), hashed_password)
    except Exception:
        return False
