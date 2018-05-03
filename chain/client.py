import asyncio
import sys

from chain.p2p import P2PServer as Server
from chain.log import logger

if len(sys.argv) != 5:
    print("Usage: python set.py <bootstrap node> <bootstrap port> <key> <value>")
    sys.exit(1)


loop = asyncio.get_event_loop()
loop.set_debug(True)

server = Server()
server.listen(7469)
bootstrap_node = (sys.argv[1], int(sys.argv[2]))

logger.error(loop.run_until_complete(server.bootstrap([bootstrap_node])))
logger.error(loop.run_until_complete(server.set(sys.argv[3], sys.argv[4])))
logger.error(loop.run_until_complete(server.get(sys.argv[3])))

try:
    loop.run_forever()
    pass
except KeyboardInterrupt:
    logger.error('test')
    pass
finally:
    server.stop()
    loop.close()
