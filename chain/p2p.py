import random
import asyncio
import time
from typing import List, Callable, Dict
from enum import Enum, auto


import umsgpack as msgpack
from umsgpack import UnpackException
from kademlia.network import Server
from kademlia.protocol import KademliaProtocol
from kademlia.node import Node

from chain import Block, BlockChain
from chain.log import logger


class Message(Enum):
    REQUEST_LATEST_BLOCK = auto()  # == 1
    RECEIVE_LATEST_BLOCK = auto()
    REQUEST_BLOCKCHAIN = auto()
    RECEIVE_BLOCKCHAIN = auto()
    REQUEST_BLOCKS = auto()
    RECEIVE_BLOCKS = auto()
    REQUEST_TRANSACTIONS = auto()
    RECEIVE_TRANSACTIONS = auto()

    @classmethod
    def get_latest_block(cls) -> dict:
        return dict(type=cls.REQUEST_LATEST_BLOCK.value)

    @classmethod
    def send_latest_block(cls, block: Block) -> dict:
        return dict(type=cls.RECEIVE_LATEST_BLOCK.value, block=block.serialize())

    @classmethod
    def get_blocks(cls, start_index: int, end_index: int):
        return dict(type=cls.REQUEST_BLOCKS, start_index=start_index, end_index=end_index)

    @classmethod
    def send_blocks(cls, start_index: int, end_index: int, blocks: List[Block]):
        return dict(
            type=cls.RECEIVE_BLOCKS, start_index=start_index, end_index=end_index,
            blocks=[b.serialize() for b in blocks]
        )

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

    def __init__(self, server: 'P2PServer') -> None:
        self.server = server
        self.blockchain = self.server.blockchain

    def reply(self, data: dict) -> None:
        self.transport.write(msgpack.dumps(data))

    def handle_request_latest_block(self) -> None:
        self.reply(Message.send_latest_block(self.blockchain.latest_block))
        # waiting for answer, so don't close transport here

    def handle_receive_latest_block(self, block: dict) -> None:
        peer_block = Block.deserialze(block)
        latest_block = self.blockchain.latest_block
        is_added = self.blockchain.add_block(peer_block)
        if is_added:
            self.server.broadcast_message(Message.send_latest_block(peer_block))
        elif latest_block.index < peer_block.index:
            # peer is longer, ask for blockchain
            logger.debug('Having no latest block. Asking for blockchain')
            self.server.broadcast_message(Message.get_blockchain())
        else:
            # I'm on the edge!
            pass

        self.transport.close()

    def handle_request_blockchain(self):
        self.reply(Message.send_blockchain(self.blockchain))

    def handle_receive_blockchain(self, blockchain: dict):
        other_blockchain = BlockChain.deserialze(blockchain)

        if other_blockchain.length > self.blockchain.length:
            self.blockchain.replace(other_blockchain)

        self.transport.close()

    def handle_message(self, msg: bytes):
        try:
            message = msgpack.loads(msg)
            msg_type = Message(message.pop('type'))
            logger.info(f'Handling: {msg_type}')
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
        logger.debug(f'Connecting client {peername}')
        self.transport = transport

    def data_received(self, data: bytes):
        logger.debug(f'Data receive from client: {data[:20]!r}')
        self.handle_message(data)

    def connection_lost(self, exc):
        logger.debug('The client closed the connection')


class TCPClientProtocol(TCPProtocol):

    def __init__(self, server: 'P2PServer', data: bytes) -> None:
        super().__init__(server)
        self.data = data

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.debug(f'Connecting server {peername}')
        self.transport = transport
        self.transport.write(self.data)

    def data_received(self, data: bytes):
        logger.debug(f'Data receive from server: {data[:20]!r}')
        self.handle_message(data)

    def connection_lost(self, exc):
        logger.debug('The server closed the connection')


class P2PServer(Server):
    protocol_class = UDPProtocal

    def __init__(self, ksize=20, alpha=3, node_id=None, storage=None, mining=True):
        super().__init__(ksize, alpha, node_id, storage)
        self.mining = mining
        self.read_blockchain()
        self.tcp_server = None
        self.sync_loop = None

    def listen(self, port: int, interface: str='0.0.0.0') -> None:
        logger.info(f'Node {self.node.long_id} listening on {interface}:{port}')

        loop = asyncio.get_event_loop()
        listen_udp = loop.create_datagram_endpoint(
            self._create_protocol, local_addr=(interface, port)
        )
        self.transport, self.protocol = loop.run_until_complete(listen_udp)

        listen_tcp = loop.create_server(lambda: TCPProtocol(self), interface, port)
        self.tcp_server = loop.run_until_complete(listen_tcp)

        self.refresh_table()
        self.sync_blockchain()

    def stop(self):
        super().stop()

        for task in asyncio.Task.all_tasks():
            logger.debug(f'Canceling task: {task}')
            task.cancel()

        if self.tcp_server:
            self.tcp_server.close()

        if self.sync_loop:
            self.sync_loop.cancel()

    def refresh_table(self) -> None:
        logger.debug('Refreshing routing table')
        asyncio.ensure_future(self._refresh_table())
        loop = asyncio.get_event_loop()
        self.refresh_loop = loop.call_later(10, self.refresh_table)

    def get_mempool(self) -> str:
        return ''

    def read_blockchain(self) -> None:
        # read from local or init
        self.blockchain = BlockChain()

    async def _mine(self, data: str):
        # convert sync to async
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.blockchain.mine, data)

    async def mine_blockchain(self) -> None:
        if not self.mining:
            return

        data = self.get_mempool()
        while True:
            start = time.time()
            logger.debug('Start mining...')
            mined = await self._mine(data)
            if mined:
                logger.debug(f'Mined block after {time.time() - start:.2f}s, broadcasting...')
                self.broadcast_message(Message.send_latest_block(self.blockchain.latest_block))
            else:
                logger.debug(f'Mining block failed, awaiting longest chain')
                self.broadcast_message(Message.get_blockchain())
                await asyncio.sleep(3)

    def sync_blockchain(self) -> None:
        # request latest block
        self.broadcast_message(Message.get_latest_block())
        loop = asyncio.get_event_loop()
        self.sync_loop = loop.call_later(self.blockchain.interval, self.sync_blockchain)

    def broadcast_message(self, message: dict) -> None:
        asyncio.ensure_future(self.broadcast(msgpack.dumps(message)))

    def get_peers(self) -> List[Node]:
        return self.protocol.router.findNeighbors(self.node, self.alpha)

    async def connect_peer(self, ip: str, port: int, data: bytes) -> None:
        loop = asyncio.get_event_loop()
        try:
            await loop.create_connection(lambda: TCPClientProtocol(self, data), ip, port)
        except ConnectionRefusedError:
            logger.debug('Connection refused. Peer may be offline.')

    async def broadcast(self, data: bytes) -> None:
        peers = {(p.ip, p.port) for p in self.get_peers()}
        for ip, port in peers:
            await self.connect_peer(ip, port, data)
