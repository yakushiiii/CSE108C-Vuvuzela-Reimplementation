# Targets for a simple re-implementation of Vuvuzela

Setup rounds ->
collect incoming client messages for each round wrapped in 3 layers of encryption.

Setup mixing -> 
shuffle and decrypt one layer of encryption on these messages. 

Setup delivery -> 
make messages go to next hop or final mailbox (3 servers). each round a different server is the final server and each round a different server is the entry server.

Setup cover traffic ->
every client sends a message every round

Setup dead-drop -> 
clients send and receive their messages through a dead drop

Setup shared key -> 
Clients set up a shared key when they want to communicate every round. This id is what the current round's mesasge is under.

Seteup padding on every message ->
make every message the same length, so should set up padding to ensure this.