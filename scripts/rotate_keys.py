import json
import uuid
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk


def main() -> None:
    jwks_path = Path(".well-known") / "jwks.json"
    if jwks_path.exists():
        jwks = json.loads(jwks_path.read_text(encoding="utf-8"))
    else:
        jwks = {"keys": []}

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    kid = str(uuid.uuid4())

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    jwk_key = jwk.construct(public_pem, algorithm="RS256")
    jwk_dict = json.loads(jwk_key.to_json())
    jwk_dict.update({"kid": kid, "use": "sig"})

    jwks["keys"].append(jwk_dict)
    jwks_path.parent.mkdir(parents=True, exist_ok=True)
    jwks_path.write_text(json.dumps(jwks, indent=2), encoding="utf-8")

    print("JWT_KID=", kid)
    print("JWT_PRIVATE_KEY=\n", private_pem)
    print("JWT_PUBLIC_KEY=\n", public_pem)


if __name__ == "__main__":
    main()
