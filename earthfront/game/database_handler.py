
class DatabaseHandler:
    def __init__(self, game):
        pass

    def get_cell_data(self, position: tuple[int, int]):
        return {
            "position x": str(position[0]),
            "position y": str(position[1]),
            "% of water": "55%",
            "owner": "test"
        }