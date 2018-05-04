# minichain
No UTXO transaction system yet.


# Run
Open 3 terminals and run seperately:
```bash
python -m chain.cli 8999 --mine --debug # block time is around 5s
python -m chain.cli 9000 -b 127.0.0.1 8999 --debug  # no mining
python -m chain.cli 9001 127.0.0.1 9000 --debug --mine  # connecting second node
```
