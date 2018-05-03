import random
import asyncio
import time
from typing import Tuple, List, Callable, Dict
from enum import Enum, auto


import umsgpack as msgpack
from umsgpack import UnpackException
from kademlia.network import Server
from kademlia.protocol import KademliaProtocol
from kademlia.node import Node

from chain import Block, BlockChain
from chain.log import logger

Address = Tuple[str, int]


class Message(Enum):
    REQUEST_LATEST_BLOCK = auto()  # == 1
    RECEIVE_LATEST_BLOCK = auto()
    REQUEST_BLOCKCHAIN = auto()
    RECEIVE_BLOCKCHAIN = auto()
    REQUEST_TRANSACTIONS = auto()
    RECEIVE_TRANSACTIONS = auto()

    @classmethod
    def get_latest_block(cls) -> dict:
        return dict(type=cls.REQUEST_LATEST_BLOCK.value)

    @classmethod
    def send_latest_block(cls, block: Block) -> dict:
        return dict(type=cls.RECEIVE_LATEST_BLOCK.value, block=block.serialize())

    @classmethod
    def get_blockchain(cls) -> dict:
        return dict(type=cls.REQUEST_BLOCKCHAIN.value)

    @classmethod
    def send_blockchain(cls, blockchain: BlockChain) -> dict:
        return dict(type=cls.RECEIVE_BLOCKCHAIN.value, blockchain=blockchain.serialize())


class UDPProtocal(KademliaProtocol):

    def getRefreshIDs(self) -> List[bytes]:
        '''
        Monkey patch, update random buckets like Ethereum instead of outdated buckets
        '''
        all_buckets = self.router.buckets
        assert all_buckets

        ids = []
        count = max(1, len(all_buckets) // 3)
        for bucket in random.sample(all_buckets, count):
            rid = random.randint(*bucket.range).to_bytes(20, byteorder='big')
            ids.append(rid)
        return ids


class TCPProtocol(asyncio.Protocol):

    def __init__(self, blockchain: BlockChain) -> None:
        self.blockchain = blockchain

    def reply(self, data: dict) -> None:
        self.transport.write(msgpack.dumps(data))

    def handle_request_latest_block(self) -> None:
        self.reply(Message.send_latest_block(self.blockchain.latest_block))

    def handle_receive_latest_block(self, block: dict) -> None:
        peer_block = Block.deserialze(block)
        latest_block = self.blockchain.latest_block
        is_added = self.blockchain.add_block(peer_block)
        if not is_added and latest_block.index < peer_block.index:
            # ask for blockchain
            self.reply(Message.get_blockchain())

    def handle_request_blockchain(self):
        self.reply(Message.send_blockchain(self.blockchain))

    def handle_receive_blockchain(self, blockchain: dict):
        other_blockchain = BlockChain.deserialze(blockchain)

        if other_blockchain.length < self.blockchain.length:
            self.reply(Message.send_blockchain(self.blockchain))
        elif other_blockchain.length > self.blockchain.length:
            self.blockchain.replace(other_blockchain)

    def handle_message(self, msg: bytes):
        try:
            message = msgpack.loads(msg)
            logger.info(f'Handling: {message}')
            msg_type = Message(message.pop('type'))
            func_mapping: Dict[Message, Callable] = {
                Message.REQUEST_LATEST_BLOCK: self.handle_request_latest_block,
                Message.RECEIVE_LATEST_BLOCK: self.handle_receive_latest_block,
                Message.REQUEST_BLOCKCHAIN: self.handle_request_blockchain,
                Message.RECEIVE_BLOCKCHAIN: self.handle_receive_blockchain,
            }
            func_mapping[msg_type](**message)
        except (UnpackException, KeyError, ValueError) as e:
            logger.error('Unknown message received')
            logger.error(f'{e}')

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.debug(f'Connection from {peername}')
        self.transport = transport

    def data_received(self, data: bytes):
        logger.debug(f'Data receive: {data!r}')
        self.handle_message(data)

        logger.debug('Close the client socket')
        self.transport.close()


class P2PServer(Server):
    protocol_class = UDPProtocal

    def __init__(self, ksize=20, alpha=3, node_id=None, storage=None, mining=True):
        super().__init__(ksize, alpha, node_id, storage)
        self.mining = mining
        self.watching_loops = []
        self.read_blockchain()

    def listen(self, port, interface='0.0.0.0'):
        logger.info(f'Node {self.node.long_id} listening on {interface}:{port}')

        loop = asyncio.get_event_loop()
        listen_udp = loop.create_datagram_endpoint(
            self._create_protocol, local_addr=(interface, port)
        )
        self.transport, self.protocol = loop.run_until_complete(listen_udp)

        listen_tcp = loop.create_server(lambda: TCPProtocol(self.blockchain), interface, port)
        self.tcp_server = loop.run_until_complete(listen_tcp)
        # finally, schedule refreshing table
        self.refresh_table()
        asyncio.ensure_future(self.mine_blockchain(self.get_mempool()))
        self.sync_blockchain()

    def stop(self):
        super().stop()

        for loop in self.watching_loops:
            loop.cancel()

        print(self.blockchain.blocks)

    def refresh_table(self) -> None:
        logger.debug('Refreshing routing table')
        asyncio.ensure_future(self._refresh_table())
        loop = asyncio.get_event_loop()
        self.watching_loops.append(
            loop.call_later(10, self.refresh_table)
        )

    def get_mempool(self) -> str:
        return ''

    def read_blockchain(self) -> None:
        # read from local or init
        self.blockchain = BlockChain()

    async def mine_blockchain(self, data: str) -> None:
        if not self.mining:
            return

        while True:
            start = time.time()
            logger.debug('Start mining...')
            self.blockchain.mine(data)
            logger.debug(f'Mined block after {time.time() - start:.2f}s, broadcasting...')
            await self.broadcast(
                msgpack.dumps(Message.send_latest_block(self.blockchain.latest_block))
            )

    def sync_blockchain(self) -> None:
        # request latest block
        asyncio.ensure_future(self.broadcast(
            msgpack.dumps(Message.get_latest_block())
        ))

        loop = asyncio.get_event_loop()
        self.watching_loops.append(
            loop.call_later(self.blockchain.interval * 2, self.sync_blockchain)
        )

    def get_peers(self) -> List[Node]:
        return self.protocol.router.findNeighbors(self.node, self.alpha)

    async def broadcast(self, data: bytes):
        peers = {(p.ip, p.port) for p in self.get_peers()}
        loop = asyncio.get_event_loop()
        resp: bytes = None
        for ip, port in peers:
            reader, writer = await asyncio.open_connection(ip, port, loop=loop)
            writer.write(data)
            resp = await reader.read(-1)
            logger.debug(f'[Connecting to {ip}:{port}] Sending {data}, Receiving {resp}')
            writer.close()

        if resp:
            # proxy the response to self tcp server
            ip, port = self.tcp_server.sockets[0].getsockname()
            reader, writer = await asyncio.open_connection(ip, port, loop=loop)
            writer.write(resp)
            writer.close()
