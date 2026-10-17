from slowapi import Limiter
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """レート制限のキー（クライアント IP）。

    Render は Cloudflare の背後にあり、X-Forwarded-For は「クライアントが付けた値…, 実IP, プロキシ」
    の形になる（Render は上書きせず右に追記する）。先頭は偽装できるため使わない。
    1. CF-Connecting-IP（Cloudflare が設定する。クライアントが付けたものはエッジで拒否される）
    2. X-Forwarded-For の右から2番目（実IP の位置）
    3. request.client.host（ローカル開発・ヘッダが無い場合）
    """
    cf = request.headers.get("cf-connecting-ip")
    if cf and cf.strip():
        return cf.strip()
    xff = request.headers.get("x-forwarded-for")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[-2]
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=get_client_ip)
