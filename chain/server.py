import asyncio
import sys

from chain.p2p import P2PServer as Server
from chain.log import logger


server = Server()
server.listen(int(sys.argv[1]))


loop = asyncio.get_event_loop()
loop.set_debug(True)
if len(sys.argv) > 2:
    res = loop.run_until_complete(server.bootstrap([(sys.argv[2], int(sys.argv[3]))]))
    print(res)
print(server.protocol, server.get_peers())

try:
    loop.run_forever()
except KeyboardInterrupt:
    logger.error('test')
    pass
finally:
    server.stop()
    loop.close()
