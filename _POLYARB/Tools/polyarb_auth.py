# INTELLITRADE — DrTelemon Elite Tech Conglomerate. Proprietary.
import json, logging, os, time
from dataclasses import dataclass
from eth_account import Account
from eth_account.messages import encode_typed_data

logger = logging.getLogger("polyarb.auth")

AUTH_FILE = os.path.expanduser("~/.claude/skills/_POLYARB/api_creds.json")
CLOB_BASE = "https://clob.polymarket.com"

@dataclass
class Credentials:
    api_key: str
    secret: str
    passphrase: str
    owner: str
    expires: float = 0

def _fetch(url: str, data: dict | None = None, headers: dict | None = None, retries: int = 3):
    from urllib.request import urlopen, Request
    import json as j
    for attempt in range(retries):
        try:
            body = j.dumps(data).encode() if data else None
            req = Request(url, data=body, headers={
                "User-Agent": "polyarb/1.0", "Accept": "application/json",
                "Content-Type": "application/json", **(headers or {})
            })
            with urlopen(req, timeout=15) as r:
                return j.loads(r.read().decode())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise

def create_api_key(private_key: str) -> Credentials:
    acct = Account.from_key(private_key)
    ts = int(time.time())
    msg = {
        "domain": {"name": "Polymarket API", "version": "1"},
        "types": {
            "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}],
            "CreateApiKey": [
                {"name": "action", "type": "string"},
                {"name": "timestamp", "type": "uint256"},
            ],
        },
        "primaryType": "CreateApiKey",
        "message": {"action": "create_api_key", "timestamp": ts},
    }
    signed = Account.sign_typed_data(acct.key, msg)
    data = {
        "signature": signed.signature.hex(),
        "timestamp": ts,
        "owner": acct.address,
    }
    try:
        resp = _fetch(f"{CLOB_BASE}/auth", data)
    except Exception as e:
        logger.error("L1 auth failed: %s", e)
        raise
    creds = Credentials(
        api_key=resp["api_key"],
        secret=resp["secret"],
        passphrase=resp["passphrase"],
        owner=acct.address,
        expires=time.time() + 86400 * 30,
    )
    _save(creds)
    logger.info("API key created for %s", acct.address[:10])
    return creds

def _save(creds: Credentials):
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    with open(AUTH_FILE, "w") as f:
        json.dump(creds.__dict__, f, indent=2)

def load_creds() -> Credentials | None:
    if not os.path.exists(AUTH_FILE):
        return None
    with open(AUTH_FILE) as f:
        d = json.load(f)
    return Credentials(**d)

def l2_headers(private_key: str, creds: Credentials) -> dict:
    acct = Account.from_key(private_key)
    ts = int(time.time())
    msg = {
        "domain": {"name": "Polymarket API", "version": "1"},
        "types": {
            "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}],
            "Authenticate": [
                {"name": "action", "type": "string"},
                {"name": "apiKey", "type": "string"},
                {"name": "timestamp", "type": "uint256"},
            ],
        },
        "primaryType": "Authenticate",
        "message": {"action": "authentication", "apiKey": creds.api_key, "timestamp": ts},
    }
    signed = Account.sign_typed_data(acct.key, msg)
    return {
        "POLY_API_KEY": creds.api_key,
        "POLY_SIGNATURE": signed.signature.hex(),
        "POLY_TIMESTAMP": str(ts),
        "POLY_PASSPHRASE": creds.passphrase,
    }

def ensure_auth(private_key: str) -> tuple[Credentials, dict]:
    creds = load_creds()
    if not creds or creds.expires < time.time():
        creds = create_api_key(private_key)
    headers = l2_headers(private_key, creds)
    return creds, headers

def sign_order(private_key: str, order: dict) -> str:
    acct = Account.from_key(private_key)
    domain = {
        "name": "Polymarket CTF",
        "version": "1",
        "chainId": 137,
        "verifyingContract": "0xCcF80000...",
    }
    msg = {
        "domain": domain,
        "primaryType": "Order",
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Order": [
                {"name": "maker", "type": "address"},
                {"name": "side", "type": "uint8"},
                {"name": "tokenId", "type": "uint256"},
                {"name": "price", "type": "uint256"},
                {"name": "size", "type": "uint256"},
                {"name": "feeRateBps", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "expiration", "type": "uint256"},
            ],
        },
        "message": order,
    }
    signed = Account.sign_typed_data(acct.key, msg)
    return signed.signature.hex()
