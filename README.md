# minichain

Powered by asyncio.

UTXO model transaction system not yet.

# How to run

Open 3 terminals and run seperately:
```bash
python -m chain.cli 8999 --mine --debug # block time is around 5s
python -m chain.cli 9000 -b 127.0.0.1 8999 --debug  # no mining
python -m chain.cli 9001 -b 127.0.0.1 9000 --debug --mine  # connecting second node
```

# How to implement

This repo is using [Kademlia](https://github.com/bmuller/kademlia) for finding peers and syncing blockchain via simple TCP.

You can create a UDP server and a TCP server listening at the **same** port. When you have found peers by Kademlia, directly connect to that IP and port to start syncing blockchain data.

A simple example about syncing the latest block:

1. Sending `REQUEST_LATEST_BLOCK` message to a peer or peers.
2. When receiving `REQUEST_LATEST_BLOCK`, send back the message `RECEIVE_LATEST_BLOCK` with block data.
3. When receiving `RECEIVE_LATEST_BLOCK`:
    1. Check the receive block is valid or not;
    2. If yes, add it to our blockchain and broadcast it to peers;
    3. If no, check if the block is ahead;
        1. If yes, sending `REQUEST_BLOCKCHAIN` to peers and wait for the incoming blockchain data.
        2. If no, which means our blockchain is the freshest, do nothing.

# I want to know more..

Go check [this](https://blockchaindemo.io/) and [this](https://coindemo.io/) to know the basics and stay tuned with this repo!
