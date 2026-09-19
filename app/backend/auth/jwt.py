from datetime import datetime, timedelta

from jose import JWTError, jwt

from config import ACCESS_TOKEN_EXPIRE_DAYS, JWT_ALGORITHM, SECRET_KEY

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY が未設定です。openssl rand -hex 32 で生成し環境変数に設定してください。"
    )


def create_access_token(data: dict) -> str:
    """JWTトークンを発行する（有効期限30日）"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> str | None:
    """トークンを検証し、ユーザー名を返す。無効・期限切れの場合はNoneを返す。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
