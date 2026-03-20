#EXTRA FUNCTIONS

""""
    for printing keys for testing

    private_bytes = client_1.private_key.private_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PrivateFormat.Raw,
    encryption_algorithm=serialization.NoEncryption()
    )  

    print(private_bytes.hex())

    public_bytes = client_1.public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
    )
    print("\n")
    print(public_bytes.hex())
"""

"""
#creating a shared secret
def shared_secret(self_private_key, other_public_key):
    shared_key = self_private_key.exchange(other_public_key)
    return shared_key
"""

#CLIENT
""""
            with open("directory.json", "r") as f:
                parsed_json = json.load(f)

            if "users" not in parsed_json:
                print("directory.json is missing 'users'")
                self.partner = None
                return None

            while self.partner not in parsed_json["users"]:
                print("User does not exist. Please try again.")
                self.partner = input("Enter the username of client you want to communicate with: ")
                while self.partner == "" or self.partner == "\n":
                    print("Not a valid user.")
                    self.partner = input("Enter the username of client you want to communicate with: ")

            public_key_hex = parsed_json["users"][self.partner]["public_key"]
            public_key_bytes = bytes.fromhex(public_key_hex)
            self.partner_pubK = x25519.X25519PublicKey.from_public_bytes(public_key_bytes)
            self.shared_secret = encryption.shared_secret(self.private_key, self.partner_pubK)
            self.partner_lookup_in_progress = False
            print(f"Now communicating with {self.partner}")
            print(f"Caution: please allow at least a minute to receive all partner messages before you quit, if not they will be lost.")
            return self.partner

        finally:
            self.partner_lookup_in_progress = False
        
        with self.sock_lock:
            partner_pubK_req = {"type": "PARTNER_PUBLIC_KEY_REQUEST"}
            req_bytes = json.dumps(partner_pubK_req).encode()
            send_packet(sock, req_bytes)
        """

"""
def try_decrypt(key, nonce, ciphertext):
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext
    except Exception:
        return None

result = try_decrypt(key, nonce, ciphertext)"
"""