import unittest
from unittest.mock import patch
from chainsearch.searcher import Search
from chainsearch.models import GenericContract, GenericERC20

# TODO better testing
class SearchTests(unittest.TestCase):

    @patch("chainsearch.searcher.Web3")
    def test_search_instance_raises(self, web3) -> None:
        self.assertRaises(ValueError, Search, **{"provider": ""})
        self.assertRaises(ValueError, Search, **{"provider": "", "address": "0xfake"})
        self.assertRaises(ValueError, Search, **{"provider": "", "abi": "{fake}"})

        contract = GenericContract(address=None)
        self.assertRaises(ValueError, Search, **{"provider": "", "contract_model": contract})

    @patch("chainsearch.searcher.Search._get_event")
    @patch("chainsearch.searcher.Web3")
    def test_get_events_validates(self, web3, get_event) -> None:
        web3.return_value.eth.contract.return_value.events = ["event1", "event2"]
        web3.return_value.eth.blockNumber = 100
        con = GenericContract(address="0xfake")
        searcher = Search("", contract_model=con)
        args = {
            "from_block": 5,
            "to_block": 1,
            "n_blocks_ago": None
        }
        self.assertRaises(ValueError, searcher.get_events, **args)
        args = {
            "from_block": 5,
            "to_block": 10,
            "n_blocks_ago": 3
        }
        self.assertRaises(ValueError, searcher.get_events, **args)
        args = {
            "from_block": -5,
            "to_block": 10,
            "n_blocks_ago": None
        }
        self.assertRaises(ValueError, searcher.get_events, **args)
        args = {
            "from_block": None,
            "to_block": None,
            "n_blocks_ago": 500
        }
        self.assertRaises(ValueError, searcher.get_events, **args)

