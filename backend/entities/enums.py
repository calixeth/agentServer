from enum import Enum


class ChainType(str, Enum):
    """Blockchain types supported for wallet authentication"""
    ETHEREUM = "ethereum"
    SOLANA = "solana"
    # BSC = "bsc"
    # POLYGON = "polygon"
    # AVALANCHE = "avalanche"