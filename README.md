# Chainsearch
#### A lighweight blockchain event explorer

### Requirements:

`python >= 3.8`
`pandas >= 1.4`
`web3 == 5.28.0`

This little module can, provided an abi and a contract address, download all the events emitted by that contract
as a pandas dataframe. We can test it with the LINK token:


```python
from chainsearch.searcher import Search
from chainsearch.models import GenericERC20

provider = "<provider address such as an infura api key>"
LINK_address = "0x514910771af9ca656af840dff83e8264ecf986ca"

contract = GenericERC20(address=LINK_address)
searcher = Search(provider, contract_model=contract)
result = searcher.get_events(n_blocks_ago=5000)

print("Transfer events:")
print(result["Transfer"].head(5).to_markdown())
```

    Transfer events:
    |    |   block_n | from                                       | to                                         |                 value |
    |---:|----------:|:-------------------------------------------|:-------------------------------------------|----------------------:|
    |  0 |  14559201 | 0x28C6c06298d514Db089934071355E5743bf21d60 | 0x2a0a5d32CF3f34AA7Ec3233cA665975764f07FE5 | 270409250000000000000 |
    |  1 |  14559202 | 0xFAD57d2039C21811C8F2B5D5B65308aa99D31559 | 0x05683C2ca8CdA1688438C5c75568Ee0E2F6E750d | 275000000000000000000 |
    |  2 |  14559202 | 0xac5A2c404EbBa22a869998089AC7893ff4E1F0a7 | 0x05683C2ca8CdA1688438C5c75568Ee0E2F6E750d | 225000000000000000000 |
    |  3 |  14559208 | 0x55f67C402525143E0E9b9611fe726B2fF643e37c | 0x0a5f999BaBf22E2F37a64D55Ac080D46Bb955A99 | 920000000000000000000 |
    |  4 |  14559221 | 0xa6Cc3C2531FdaA6Ae1A3CA84c2855806728693e8 | 0x407e99b20d61f245426031dF872966953909e9d3 |   3108444588605477013 |
    

`get_events()` returns a dict where event names are keys and dataframes with event data are values. Start and end blocks are easy to condigure:


```python
result = searcher.get_events()  # To retrieve data since the blockchain started
result = searcher.get_events(from_block=100)  # To ask for data since block nº100 to latest block
result = searcher.get_events(from_block=100, to_block=200)  # To specify a block range
```

The contract can be defined by a custom abi or using one of the provided models, as the project comes wiht several abi models for popular contract types:


```python
searcher = Search(provider, address='<some address>', abi='<abi of a contract>')  # Both as a str
# or
contract = GenericERC20(address='<any erc20 address>')
searcher = Search(provider, contract_model=contract)
```

The query will be batched by default to 10 batches and 10 threads. For queries that explore a big number of blocks (more than 1 million) and/or popular contracts this can be tweaked:


```python
searcher.workers = 100
searcher.batches = 50
```

If infura is used then some times the max query size will be reached (10k records).
In that scenario the module will divide the batch that caused the error into smaller
batches and try again. This process will continue recursively until batch size is 
small enough so infura actually returns a valid result. This may be a source of 
delays and is almost guaranteed to happen if the block range to explore is too big
while using a popular contract (like LINK).