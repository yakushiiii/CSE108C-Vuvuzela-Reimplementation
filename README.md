# Targets for a simple re-implementation of Vuvuzela

Setup rounds ->
collect incoming client messages for each round wrapped in 3 layers of encryption.

Setup mixing -> 
shuffle and decrypt one layer of encryption on these messages. Each server must remember the order they sent the messages in.

Setup delivery -> 
make messages go to next hop or final mailbox (3 servers). each round a different server is the final server and each round a different server is the entry server. 

Setup cover traffic ->
every client sends a message every round

Setup dead-drop -> 
clients send their messages to a dead drop

Setup shared key -> 
Clients set up a shared key when they want to communicate every round. This id is what the current round's message is under. Use hashing for the id

