import sqlite3
from .models import ChunkData
from .logger import Logger
from .gen_chunk_bdd import ChunkDataExtractor

logger = Logger()


class DatabaseHandler:
    def __init__(self, game, db_name="data/chunk_base.db"):
        self.game = game
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cur = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """Crée la table chunks si elle n'existe pas"""
        try:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS chunk (
                    position TEXT PRIMARY KEY,
                    oil      INTEGER,
                    gold     INTEGER,
                    iron     INTEGER,
                    copper   INTEGER,
                    coal     INTEGER,
                    water    INTEGER,
                    wood     INTEGER
                )
            """)
            self.conn.commit()
            logger.info("Table 'chunk' créée ou déjà existante")
        except Exception as e:
            logger.error(f"Erreur création table : {e}")

    def generate_world(self, seed, width, height, on_progress=None):
        logger.info(f"Génération du monde (seed={seed}, taille={width}x{height})...")

        # Nouvelle connexion propre pour ce thread
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()

        cur.execute("DELETE FROM chunk")
        conn.commit()
        logger.info("Table chunk vidée")

        extractor = ChunkDataExtractor(seed=seed)
        chunk_count = 0

        for x in range(width):
            for y in range(height):
                chunk_data = extractor.get_chunk_data(x, y)
                position_str = f"{chunk_data.position[0]};{chunk_data.position[1]}"
                cur.execute("""
                    INSERT OR REPLACE INTO chunk
                    (position, oil, gold, iron, copper, coal, water, wood)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (position_str, chunk_data.oil, chunk_data.gold, chunk_data.iron,
                      chunk_data.copper, chunk_data.coal, chunk_data.water, chunk_data.wood))
                chunk_count += 1

                if chunk_count % 50 == 0:  # commit toutes les 50 insertions (plus rapide)
                    conn.commit()

                if on_progress is not None:
                    on_progress(chunk_count)

        conn.commit()  # commit final
        conn.close()

        logger.info(f"✅ {chunk_count} chunks générés et insérés !")
        return chunk_count

    def insert_chunk(self, chunk_data: ChunkData) -> bool:
        """Insère un chunk dans la BDD"""
        try:
            query = """
                INSERT OR REPLACE INTO chunk
                (position, oil, gold, iron, copper, coal, water, wood)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            position_str = f"{chunk_data.position[0]};{chunk_data.position[1]}"
            self.cur.execute(query, (
                position_str,
                chunk_data.oil,
                chunk_data.gold,
                chunk_data.iron,
                chunk_data.copper,
                chunk_data.coal,
                chunk_data.water,
                chunk_data.wood,
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erreur insertion chunk {chunk_data.position} : {e}")
            return False

    def get_chunk_data(self, x: int, y: int) -> ChunkData | None:
        """Récupère un chunk depuis la BDD"""
        try:
            position_str = f"{x};{y}"
            self.cur.execute("""
                SELECT position, oil, gold, iron, copper, coal, water, wood
                FROM chunk WHERE position = ?
            """, (position_str,))
            row = self.cur.fetchone()

            if row is None:
                logger.warning(f"Chunk {x},{y} non trouvé dans la BDD")
                return None

            chunk       = ChunkData((x, y))
            chunk.oil   = row[1]
            chunk.gold  = row[2]
            chunk.iron  = row[3]
            chunk.copper = row[4]
            chunk.coal  = row[5]
            chunk.water = row[6]
            chunk.wood  = row[7]
            return chunk

        except Exception as e:
            logger.error(f"Erreur récupération chunk {x},{y} : {e}")
            return None

    def chunk_exists(self, x: int, y: int) -> bool:
        """Vérifie si un chunk existe dans la BDD"""
        position_str = f"{x};{y}"
        self.cur.execute("SELECT 1 FROM chunk WHERE position = ?", (position_str,))
        return self.cur.fetchone() is not None

    def get_world_info(self):
        """Retourne des infos sur le monde chargé"""
        self.cur.execute("SELECT COUNT(*) FROM chunk")
        chunk_count = self.cur.fetchone()[0]

        self.cur.execute("SELECT SUM(gold), SUM(iron), SUM(oil) FROM chunk")
        totals = self.cur.fetchone()

        return {
            "chunk_count": chunk_count,
            "total_gold":  totals[0] or 0,
            "total_iron":  totals[1] or 0,
            "total_oil":   totals[2] or 0,
        }

    def close_connection(self):
        """Ferme la connexion à la BDD"""
        self.conn.close()
        logger.info("Connexion BDD fermée")