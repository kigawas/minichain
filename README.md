# minichain

[![License](https://img.shields.io/github/license/kigawas/minichain.svg)](https://github.com/kigawas/minichain)
[![Travis branch](https://img.shields.io/travis/kigawas/minichain/master.svg)](https://travis-ci.org/kigawas/minichain)
[![Codecov](https://img.shields.io/codecov/c/github/kigawas/minichain.svg)](https://codecov.io/gh/kigawas/minichain)

-   Using the freshest Python 3 syntax
-   UTXO model
-   Nakamoto consensus
-   P2P part is powered by `asyncio` and [`kademlia`](https://github.com/bmuller/kademlia)
-   Elliptic curve part is powered by [`coincurve`](https://github.com/ofek/coincurve)

## How to run

Install dependencies first by running `pip install -r requirements.txt`.

Open 3 terminals and run seperately:

```bash
python -m chain 8999 --mine --debug # block time is around 5s
python -m chain 9000 -b 127.0.0.1 8999 --debug  # no mining
python -m chain 9001 -b 127.0.0.1 9000 --debug --mine  # connecting second node
```

## How to implement

### Find peers

This repo is leveraging [Kademlia algorithm](https://github.com/bmuller/kademlia) for finding peers via UDP and syncing blockchain via TCP.

You can create a UDP server and a TCP server listening at the **same port** to simplify the logic. When it's found peers by Kademlia, our node just directly connects to that IP and port to start syncing blockchain data.

### Sync blocks

A simple example about syncing the latest block:

1.  Sending `REQUEST_LATEST_BLOCK` message to a peer or peers.
2.  When receiving `REQUEST_LATEST_BLOCK`, send back the message `RECEIVE_LATEST_BLOCK` with block data.
3.  When receiving `RECEIVE_LATEST_BLOCK`:
    1.  Check the received block is valid or not;
    2.  If valid, add it to our blockchain and broadcast it to peers;
    3.  Else, check if the block is ahead;
        1.  If ahead, sending `REQUEST_BLOCKCHAIN` to peers and wait for the incoming blockchain data.
        2.  Else, which means our blockchain is the freshest, do nothing.

For more details, check the [`p2p.py`](https://github.com/kigawas/minichain/blob/master/chain/p2p.py) code. The logic is simple, but more powerful protocols (like log replication of Raft protocol) are based on the simple ideas behind the implementation here.

## Reference

Go check [this](https://blockchaindemo.io/) and [this](https://coindemo.io/) to learn the basics and stay tuned with this repo!
