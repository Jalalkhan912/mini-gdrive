from fastapi import Header, HTTPException, status


def current_user(x_user_id: str = Header(...)) -> str:
    """Temporary identity stub: trusts the X-User-Id header.

    Anyone can claim any user ID, so this is for local development only.
    Replace with JWT verification in milestone 4.
    """
    user_id = x_user_id.strip()
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing user identity")
    return user_id
