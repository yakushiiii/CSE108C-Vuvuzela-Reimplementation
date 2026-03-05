import asyncio
from config import Rounds


# Run Re-implementation of Vuvuzela
# Store temp public key for users


#maybe this file to initiliaze whole thing including Rounds system

#initialize and start the rounds system
#this will be accessed by all other files
async def main():
    rounds = Rounds()
    #asyncio.create_task(rounds.run())
    asyncio.create_task(rounds.serverA())    #<-- implement later
    #asyncio.create_task(start_serverB)       <-- implement later
    #asyncio.create_task(start_serverC)       <-- implement later

    # this line keeps the Rounds going forever
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())


## client joining
# when a client joins send them all the information so they can sync with the Rounds despite being on different machines
# client should resync ever 30 seconds
# to account for latency measure the time of the request