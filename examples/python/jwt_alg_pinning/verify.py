# Author: Sandeep Belgavi. Original teaching example; all data is synthetic.

"""Why a JWT verifier must choose the algorithm itself.

The vulnerable verifier takes the algorithm from the token, so an HMAC signature keyed with a public key passes.
The pinned verifier compares the header with configuration and rejects it before any signature check.
Standard library only; RSA verification itself belongs to a maintained JOSE library.
"""
import base64
import hashlib
import hmac
import json


class Forged(Exception):
    pass


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign_hs256(payload, secret):
    head = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = b64url(json.dumps(payload).encode())
    sig = hmac.new(secret, f"{head}.{body}".encode("ascii"), hashlib.sha256).digest()
    return f"{head}.{body}.{b64url(sig)}"


def verify_header_chooses(token, public_key_pem):
    """VULNERABLE: trusts the header, and treats the public key text as an HMAC secret when alg is HS256."""
    head, body, sig = token.split(".")
    header = json.loads(b64url_decode(head))
    if header.get("alg") == "HS256":
        secret = public_key_pem.encode()
        want = hmac.new(secret, f"{head}.{body}".encode("ascii"), hashlib.sha256).digest()
        if hmac.compare_digest(want, b64url_decode(sig)):
            return json.loads(b64url_decode(body))
        raise Forged("bad signature")
    raise Forged("only HS256 is modelled here")


def verify_pinned(token, public_key_pem, expected_alg="RS256"):
    head, body, sig = token.split(".")
    header = json.loads(b64url_decode(head))
    if header.get("alg") != expected_alg:
        raise Forged(f"alg {header.get('alg')!r}, expected {expected_alg!r}")
    raise NotImplementedError("Signature verification: use a maintained JOSE library for RS256.")


if __name__ == "__main__":
    public_pem = "-----BEGIN PUBLIC KEY-----\nsynthetic-example\n-----END PUBLIC KEY-----\n"
    forged = sign_hs256({"sub": "geetha", "role": "admin"}, public_pem.encode())
    print("vulnerable verifier accepts:", verify_header_chooses(forged, public_pem))
    try:
        verify_pinned(forged, public_pem)
    except Forged as err:
        print("pinned verifier rejects:", err)
