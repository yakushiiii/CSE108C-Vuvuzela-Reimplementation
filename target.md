# Targets for a simple re-implementation of Vuvuzela

Setup rounds ->
collect incoming client messages for each round wrapped in 3 layers of encryption.

Setup mixing -> 
shuffle and decrypt one layer of encryption on these messages

Setup delivery -> 
make messages go to next hop or final mailbox (3 servers)

Setup cover traffic ->
every client sends a message every round
