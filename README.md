# minichain

[![License](https://img.shields.io/github/license/kigawas/minichain.svg)](https://github.com/kigawas/minichain)
[![Travis branch](https://img.shields.io/travis/kigawas/minichain/master.svg)](https://travis-ci.org/kigawas/minichain)
[![Codecov](https://img.shields.io/codecov/c/github/kigawas/minichain.svg)](https://codecov.io/gh/kigawas/minichain)

- Using the freshest Python 3 syntax
- UTXO model
- P2P part is powered by `asyncio` and [`kademlia`](https://github.com/bmuller/kademlia)
- Elliptic curve part is powered by [`coincurve`](https://github.com/ofek/coincurve)

# How to run

Install dependencies first by running `pip install -r requirements.txt`.

Open 3 terminals and run seperately:

```bash
python -m chain 8999 --mine --debug # block time is around 5s
python -m chain 9000 -b 127.0.0.1 8999 --debug  # no mining
python -m chain 9001 -b 127.0.0.1 9000 --debug --mine  # connecting second node
```

# How to implement

This repo is using [Kademlia algorithm](https://github.com/bmuller/kademlia) for finding peers via UDP and syncing blockchain via TCP.

You can create a UDP server and a TCP server listening at the **same port**. When you have found peers by Kademlia, directly connect to that IP and port to start syncing blockchain data.

A simple example about syncing the latest block:

1. Sending `REQUEST_LATEST_BLOCK` message to a peer or peers.
2. When receiving `REQUEST_LATEST_BLOCK`, send back the message `RECEIVE_LATEST_BLOCK` with block data.
3. When receiving `RECEIVE_LATEST_BLOCK`:
    1. Check the received block is valid or not;
    2. If valid valid, add it to our blockchain and broadcast it to peers;
    3. Else, check if the block is ahead;
        1. If ahead, sending `REQUEST_BLOCKCHAIN` to peers and wait for the incoming blockchain data.
        2. Else, which means our blockchain is the freshest, do nothing.

# Any reference?

Go check [this](https://blockchaindemo.io/) and [this](https://coindemo.io/) to learn the basics and stay tuned with this repo!
