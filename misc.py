    
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