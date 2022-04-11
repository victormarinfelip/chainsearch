from typing import Optional, List, Type, Dict, Union
from chainsearch.models import ContractModel, GenericContract
from datetime import datetime, timedelta
import pandas as pd
from pandas import DataFrame
from multiprocessing.dummy import Pool

from web3 import Web3
from web3.contract import ContractEvent



class Search(object):

    def __init__(self,
                provider: str,
                address: Optional[str] = None,
                abi: Optional[str] = None,
                contract_model: Optional[ContractModel] = None
                ):
        self.web3 = Web3(Web3.HTTPProvider(provider))
        self._batches = 10
        self._workers = 10
        self._current_block = 1
        self._current_block_last_updated = datetime.now() - timedelta(hours=10)

        # Let's do some validation
        errmsg = "address and abi, or address and contract_model, or" \
                 "contract model with address must be passed."
        if contract_model is None:
            if address is None or abi is None:
                raise ValueError(errmsg)
            if not (isinstance(address, str) and isinstance(abi, str)):
                raise TypeError("address and abi must be string")
        else:
            if contract_model.address is None and address is None:
                raise ValueError(errmsg)

        # Now let's define our contract.
        self.contract = contract_model
        if self.contract is None:
            # If none was passsed then we create our own.
            self.contract = GenericContract(address=address, abi=abi)
        else:
            # And if it was specified we just update the address if needed.
            if contract_model.address is None:
                contract_model.address = address
                self.contract = contract_model

        # And this will be our deployed real contract
        self.deployed = self.web3.eth.contract(address=self.web3.toChecksumAddress(self.contract.address),
                                               abi=self.contract.abi)

    @property
    def current_block(self) -> int:
        if datetime.now() >= self._current_block_last_updated + timedelta(seconds=10):
            # Only update once every 10 secs to avoid spamming this call
            self._current_block = int(self.web3.eth.blockNumber)
            # We ask for now twice because the call will take some seconds and we want up to date data
            self._current_block_last_updated = datetime.now()
        return self._current_block

    @property
    def batches(self) -> int:
        """
        Returns the number of batches that the searcher will divide the block range into.

        :return: Number of batches.
        """
        return self._batches

    @batches.setter
    def batches(self, value: int):
        """
        Sets the number of batches
        """
        if not isinstance(value, int):
            raise TypeError
        self._batches = value

    @property
    def workers(self) -> int:
        """
        Returns the number of threads that the searcher will initially instantiate to request the batches.

        :return: Number of workers.
        """
        return self._workers

    @workers.setter
    def workers(self, value: int):
        """
        Sets the number of workers
        """
        if not isinstance(value, int):
            raise TypeError
        self._workers = value

    def get_events(self,
                   from_block: Optional[Union[int, str]] = None,
                   to_block: Optional[Union[int, str]] = None,
                   n_blocks_ago: Optional[int] = None,
                   ) -> Dict[str, DataFrame]:
        """
        Returns a dict where key: <event_name>, value: <event_data_as_dataframe>. The dataframes will have
        as many columns as attributes the event has with their names,
        and one extra column for the block number as 'block_n'.

        :param from_block: Starting block number, earliest if None. Mutually exclusive with n_blocks_ago.
        :param to_block: Ending block number, latest if None
        :param n_blocks_ago: Get data from N blocks ago. Mutually exclusive with from_block.
        :return: Returns a dict where key: <event_name>, value: <event_data_as_dataframe>.
        """
        # Let's do some checks
        if from_block is None and n_blocks_ago is None:
            from_block = 1 # This gets converted to "earliest" later.
        if from_block is not None and n_blocks_ago is not None:
            raise ValueError("You can't specify 'from_block' and 'n_blocks_ago' at the same time!")
        if n_blocks_ago is not None:
            from_block = self.current_block - n_blocks_ago
        if to_block is None:
            to_block = self.current_block
        if from_block > to_block:
            raise ValueError("Initial block is greater than final block!")
        if to_block > self.current_block:
            raise ValueError("Final block is greater than current block!")
        if from_block < 0:
            raise ValueError("Initial block can't be negative!")

        out: Dict[str, DataFrame] = {}
        for event in self.deployed.events:
            combined = self._get_event(event, from_block, to_block)
            out[event.event_name] = combined
        return out

    def _get_event(self,
                   event: Type[ContractEvent],
                   from_block: Optional[int] = None,
                   to_block: Optional[int] = None,
                   ) -> Optional[DataFrame]:
        batch_size = int((to_block - from_block) / self.batches)
        boundaries = []
        for i in range(self.batches):
            block_start = i * batch_size + from_block
            block_end = block_start + batch_size
            boundaries.append([event, block_start, block_end])
        boundaries[-1][2] = to_block # Make sure that no rounding errors exclude the last block

        with Pool(self.workers) as p:
            result = p.map(self._download_batch, boundaries)
            result = [k for k in result if k is not None]
            if len(result) > 0:
                combined = pd.concat(result)
                combined = combined.reset_index(drop=True)
                combined = combined.sort_values(by="block_n")
            else:
                combined = []
        return combined

    def _download_batch(self, args: List) -> Optional[DataFrame]:
        event, start, end = args
        batch = {
            "fromBlock": int(start),
            "toBlock": int(end)
        }
        filter_ = event.createFilter(**batch)
        """
        This can fail if infura/another provider returns an error
        In the case of infura this can happen if there are more than
        10k results in the query, so we can control for that and
        then relaunch this function but dividing the blocks to explore by 2
        recursively, so eventually this will converge to a batch size small enough
        while having big batches for less populated block ranges
        TODO: make a queue system so everything can happen in parallel properly...
        """
        try:
            entries = filter_.get_all_entries()
        except ValueError as e:
            if "query returned more than 10000 results" not in str(e):
                raise
            else:
                # Now we launch this very function twice:
                subbatches = [
                    [event, start, int((start+end)/2)],
                    [event, int((start+end)/2), end]
                ]
                with Pool(2) as p:
                    result = p.map(self._download_batch, subbatches)
                    result = [k for k in result if k is not None]
                    if len(result) > 0:
                        return pd.concat(result)
                    else:
                        return None

        if len(entries) == 0:
            return
        args = list(entries[0].args.keys())
        header = ["block_n"] + args
        data = []
        for entry in entries:
            vals = list(entry.args.values())
            block_n = entry.blockNumber
            data.append([block_n]+vals)
        df = pd.DataFrame(columns=header, data=data)
        return df
