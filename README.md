Our implementation can serve up to 17 users at a time. 




----------------------------------
How the Vuvuzela Encryption works:
----------------------------------

2 types of encryption:
    1. Message encryption (between users, used to encrypt the actual chat message)
    2. Onion encrpytion (between client and server, used to hide which dead drop the message goes to)

Step 1:
    Users generate a shared secret using Diffie Hellman(client_1_private, client_2_public) to produce a shared symmetrc key
Step 2:
    Compute the Dead Drop ID computed by hashing the shared secret + round number (so this changes every round)
Step 3:
    Encrypt the message using the shared secret computed earlier using Diffie Hellman. If the message is a dummy message we would encrypt with a fake shared secret and a fake dead drop that is uniformly generated. The dummy message is also a uniform message.
Step 4: 
    Onion encrypt the message + dead_drop_id for every server, one layer on top of the other. For each server the client creates an ephemeral key pair and sends the encrypted message with the public key, so the server can compute a shared secret and then decrypt. The client saves the symmetric keys created from this.
Step 5:
    Once the server sends back the message, the client uses its saved shared keys to decrypt each layer of the onion encrypted message it received from the servers.
Step 6: 
    Dummy messages are ignored, while the real messages are displayed for the user. 
Step 7:
    Once a new round starts do steps 1-6 again.


