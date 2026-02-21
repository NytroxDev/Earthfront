from PIL import Image
from random import Random
from .models import ChunkData


class ChunkDataExtractor:
    def __init__(self, seed=None):
        self.map_path = "./src/carte.png"
        self.img_map = Image.open(self.map_path).convert("RGB")
        self.pixels = self.img_map.load()

        # Seed pour la génération pseudo-aléatoire
        self.seed = seed if seed is not None else 42  # Seed par défaut
        self.base_random = Random(self.seed)  # Générateur de base (non utilisé directement)

    def _get_chunk_random(self, x, y):
        """
        Crée un générateur Random spécifique pour ce chunk
        en utilisant la seed de base + les coordonnées du chunk
        """
        chunk_seed = hash((self.seed, x, y)) & 0xFFFFFFFF  # Seed unique par chunk
        return Random(chunk_seed)

    def get_chunk_pixels(self, x, y):
        chunk_data = ChunkData((x, y))

        colors = {
            (120, 190, 255): "water",
            (0, 180, 0): "grass",
            (255, 255, 255): "snow",
            (220, 200, 140): "sand"
        }

        for r in range(10):
            for c in range(10):
                try:
                    pixel = self.pixels[x * 10 + r, y * 10 + c]
                    setattr(chunk_data, colors[pixel], getattr(chunk_data, colors[pixel]) + 1)
                except:
                    print(f"chunk n°{x},{y} - pixel n°{r},{c}")

        return chunk_data

    def get_chunk_data(self, x, y):
        chunk_data = self.get_chunk_pixels(x, y)

        # Utiliser le générateur random spécifique à ce chunk
        rng = self._get_chunk_random(x, y)

        if chunk_data.water >= 90 or chunk_data.sand + chunk_data.snow >= 90:
            p = rng.randint(0, 50)
            if p < 30:
                chunk_data.oil = rng.randint(10, 40)
            elif p > 40:
                chunk_data.oil = rng.randint(60, 100)

        if chunk_data.water < 90:
            ressources = ["gold", "iron", "copper", "coal"]
            for ressource in ressources:
                p = rng.randint(0, 50)
                if p < 30:
                    setattr(chunk_data, ressource, rng.randint(10, 40))
                elif p > 45:
                    setattr(chunk_data, ressource, rng.randint(60, 100))

        chunk_data.wood = int(chunk_data.grass + chunk_data.snow / 2)

        return chunk_data


# Exemple d'utilisation
if __name__ == "__main__":
    # Avec une seed spécifique
    extractor1 = ChunkDataExtractor(seed=12345)
    print("Test 1:", extractor1.get_chunk_data(70, 50))

    # Même seed = même résultat
    extractor2 = ChunkDataExtractor(seed=12345)
    print("Test 2:", extractor2.get_chunk_data(70, 50))

    # Seed différente = résultat différent
    extractor3 = ChunkDataExtractor(seed=99999)
    print("Test 3:", extractor3.get_chunk_data(70, 50))