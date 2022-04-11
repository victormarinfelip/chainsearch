import unittest
from unittest.mock import patch

from chainsearch.models import GenericContract, GenericERC20
from chainsearch.errors import NoAbiTemplateError


# TODO better testing
class ModelTests(unittest.TestCase):

    def test_generic_contract_interface(self):
        address = "address"
        abi = "abi"

        con = GenericContract(address=address, abi=abi)
        self.assertEqual(address, con.address)
        self.assertEqual(abi, con.abi)

    def test_erc20_contract_interface(self):
        address = "address"

        con = GenericERC20(address=address)
        self.assertEqual(address, con.address)
        with open("../chainsearch/abis/erc20abi.json", "r") as f:
            self.assertEqual(f.read(), con.abi)

    @patch("chainsearch.models.Path")
    def test_raises_no_template(self, path):
        # Wow this is ugly... and too dependant on the actual path
        path.return_value.parent.resolve.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = False
        address = "address"
        con = GenericERC20(address=address)
        def helper():
            return con.abi
        self.assertRaises(NoAbiTemplateError, helper)
