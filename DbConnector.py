import psycopg

class DbConnector():

    def __init__(self):
        self.dbname = "dane_lotow"
        self.user = "postgres"
        self.password = "ADM"

    # Dodac moze loty z danego dnia
    # Obsluga bledow I guess
    def getFlights(self):
        with psycopg.connect(f"dbname={self.dbname} user={self.user} password={self.password}") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM loty")

                return cur.fetchall()
            
    def getPoints(self, flightId):
         with psycopg.connect(f"dbname={self.dbname} user={self.user} password={self.password}") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM punkty WHERE lot_id = %s", [flightId])

                return cur.fetchall()
