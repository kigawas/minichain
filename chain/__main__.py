#!/usr/bin/env python
import argparse
import asyncio

from chain.p2p import P2PServer as Server
from chain.utils.log import logger

parser = argparse.ArgumentParser()

parser.add_argument("port", type=int, help="Listening port")
parser.add_argument(
    "-b",
    "--bootstrap",
    type=lambda x: int(x) if x.isdigit() else x,
    action="append",
    metavar=("IP", "PORT"),
    nargs=2,
    help="Starting by bootstrapping node, can specify multiple IPs",
)

parser.add_argument("-m", "--mine", action="store_true", help="Mining blocks")

parser.add_argument("-D", "--debug", action="store_true", help="Debug mode")

args = parser.parse_args()

server = Server(mining=args.mine)
server.listen(args.port)

loop = asyncio.get_event_loop()
loop.set_debug(args.debug)


if args.bootstrap:
    logger.debug(
        loop.run_until_complete(
            server.bootstrap([(ip, port) for ip, port in args.bootstrap])
        )
    )

try:
    if server.mining:
        loop.run_until_complete(server.mine_blockchain())
    else:
        loop.run_forever()
except KeyboardInterrupt:
    logger.debug(server.blockchain[-5:])
    server.stop()
finally:
    loop.close()
