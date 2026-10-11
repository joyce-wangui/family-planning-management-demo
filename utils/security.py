import hashlib
import hmac
import secrets


def hash_password(password):
    """Create a secure salted password hash."""
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200000
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


def verify_password(password, stored_hash):
    """Verify a password against a stored password hash."""
    try:
        salt_hex, hash_hex = stored_hash.split(":")

        salt = bytes.fromhex(salt_hex)
        stored_password_hash = bytes.fromhex(hash_hex)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            200000
        )

        return hmac.compare_digest(
            password_hash,
            stored_password_hash
        )

    except (ValueError, TypeError):
        return False
