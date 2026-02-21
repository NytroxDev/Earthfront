from dataclasses import dataclass

@dataclass
class ChunkData:

    position: tuple[int, int]

    water: int = 0
    grass: int = 0
    snow: int = 0
    sand: int = 0
    wood: int = 0

    oil: int = 0
    gold: int = 0
    iron: int = 0
    copper: int = 0
    coal: int = 0