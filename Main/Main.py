import mysql.connector

class Game:
        def __init__(self, user, password, database, home_airport_ident="EFHK"):
                self.connection = mysql.connector.connect(
                        host="localhost",
                        port="3306",
                        user=user,
                        password=password,
                        database=database
                )
                self.cursor = self.connection.cursor(dictionary=True)

                # aseta koti lentokenttä joka on nyt helsinki vantaan lentokenttä jonka ident on EFHK
                self.cursor.execute(f"SELECT * FROM airport WHERE ident = '{home_airport_ident}'")
                self.home_airport = self.cursor.fetchone()


user = "root"
password = "password"
database = "flight_game"
game = Game(user=user, password=password, database=database)
