# Server A, B, C
# Keys[private, public]
from cryptography.hazmat.primitives.asymmetric import x25519

# Raw hex strings: [private_key_hex, public_key_hex]
_raw_keys = [
    [
        "3876593914d5f5a60daa5380ccfe961b63a0890b2826219f5b05a7a5a1496d45",
        "be4420b424085b51bad775e8384cc15c6ebc22c49cf169cd8635f56caa28283e",
    ],
    [
        "3802f12fe254e95f1b793c03ed4d41ce3f4204b9f664867204c4a75f0544986c",
        "cee95351c9c12d143aa18aaf0e665b3f24aa7056d092c7f75131736ac0de6944",
    ],
    [
        "6086e59807c08d25860310fcc6921a19b0aeaad25a21895160dc689a69d3ef6d",
        "c3347a3b97843e798bf56dee5fa4485bc7453476ca47789f9b954b5496daaa1e",
    ],
]

def _load_keys(raw):
    """Convert [[priv_hex, pub_hex], ...] into X25519 key objects."""
    result = []
    for priv_hex, pub_hex in raw:
        private_key = x25519.X25519PrivateKey.from_private_bytes(bytes.fromhex(priv_hex))
        public_key  = x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
        result.append([private_key, public_key])
    return result

# keys[node_id][0] = private key object
# keys[node_id][1] = public  key object
keys = _load_keys(_raw_keys)

# Convenience aliases used by client code
serverA_public_key = keys[0][1]
serverB_public_key = keys[1][1]
serverC_public_key = keys[2][1]
