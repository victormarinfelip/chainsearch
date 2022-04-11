from os import getcwd
from pathlib import Path
from chainsearch.errors import NoAbiTemplateError
from abc import ABC, abstractmethod
from typing import Optional


class ContractModel(ABC):

    @property
    @abstractmethod
    def address(self) -> str:
        pass

    @property
    @abstractmethod
    def abi(self) -> str:
        pass

    @property
    @abstractmethod
    def evm(self) -> Optional[str]:
        pass


class GenericContract(ContractModel):

    def __init__(self,  address: str = None, abi: Optional[str] = None):
        self._address = address
        self._abi = abi

    @property
    def address(self) -> str:
        return self._address

    @property
    def abi(self) -> str:
        return self._abi

    @property
    def evm(self) -> None:
        return None


class GenericERC20(ContractModel):

    def __init__(self,  address: str = None, abi: Optional[str] = None):
        self._address = address
        self._abi = abi

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, val: str):
        self._address = val

    @property
    def abi(self) -> str:
        if self._abi is not None:
            return self._abi
        abi_path = Path(__file__).parent.resolve()/"abis"/"erc20abi.json"
        if not abi_path.exists():
            raise NoAbiTemplateError(str(abi_path))
        with open(abi_path, "r") as f:
            abi = f.read()
        return abi

    @property
    def evm(self) -> None:
        return None
