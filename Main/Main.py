import mysql.connector
import math
import webbrowser


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in kilometers
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


class Game:
    def __init__(self, user, password, database, home_airport_ident="EFHK"):
        webbrowser.open('https://ourairports.com/big-map.html')

        self.connection = mysql.connector.connect(
            host="localhost",
            port="3306",
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.connection.cursor(dictionary=True)

        try:
            self.cursor.execute("SELECT * FROM airport WHERE ident = %s", (home_airport_ident,))
            self.home_airport = self.cursor.fetchone()["ident"]
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()

        self.current_airport = self.home_airport
        self.destination_airport = None
        self.total_distance = 0
        self.name = ""

    def game_start(self):
        print("Welcome to the flight game!")
        print("Do you want to:")
        print("1. Start a new game")
        print("2. Continue a game")
        choice = input("Choose 1 or 2: ")
        try:
            choice = int(choice)
        except ValueError:
            print("Invalid choice")
            self.game_start()
            return
        if choice == 1:
            self.new_game()
        elif choice == 2:
            self.load_game()
        else:
            print("Invalid choice")
            self.game_start()

    def load_game(self):
        print("Load game")
        print("Saved games:")
        try:
            self.cursor.execute("SELECT * FROM game_data")
            games = self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
            return

        if len(games) == 0:
            print("No saved games")
            self.game_start()
            return

        for game1 in games:
            print(game1["player_name"])

        name = input("Enter your name: ")
        try:
            self.cursor.execute("SELECT * FROM game_data WHERE player_name = %s", (name,))
            game_data = self.cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
            return

        if game_data is None:
            print("Game not found")
            self.game_start()
            return

        self.name = game_data["player_name"]
        self.current_airport = game_data["current_airport_ident"]
        self.destination_airport = game_data["destination_airport_ident"]
        self.total_distance = float(game_data["total_distance"])

        self.main()

    def getClosestAirports(self):
        print("Do you want to:")
        print("1. get all large airports")
        print("2. get all medium airports")
        print("3. get all small airports")
        print("4. get all airports")
        choice = input("Choose 1-4: ")
        try:
            choice = int(choice)
        except ValueError:
            print("Invalid choice")
            self.getClosestAirports()
            return

        try:
            if choice == 1:
                self.cursor.execute("SELECT * FROM airport WHERE type = 'large_airport'")
            elif choice == 2:
                self.cursor.execute("SELECT * FROM airport WHERE type = 'medium_airport'")
            elif choice == 3:
                self.cursor.execute("SELECT * FROM airport WHERE type = 'small_airport'")
            elif choice == 4:
                self.cursor.execute("SELECT * FROM airport")
            else:
                print("Invalid choice")
                self.getClosestAirports()
                return

            all_airports = self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
            return

        try:
            self.cursor.execute("SELECT * FROM airport WHERE ident = %s", (self.current_airport,))
            current_airport = self.cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
            return

        for airport in all_airports:
            distance_to_airport = haversine_distance(airport["latitude_deg"], airport["longitude_deg"],
                                                     current_airport["latitude_deg"], current_airport["longitude_deg"])
            if distance_to_airport < 1000:
                print(airport["name"], "(", airport["ident"], ")", "is", round(distance_to_airport, 1), "km away")

    def new_game(self):
        print("New game")
        name = input("Enter your name: ")

        try:
            self.cursor.execute("SELECT * FROM game_data WHERE player_name = %s", (name,))
            if self.cursor.fetchone() is not None:
                print("Game already exists")
                self.game_start()
                return
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
            return

        self.name = name

        try:
            self.cursor.execute("SELECT * FROM airport WHERE ident = %s", (self.home_airport,))
            home_airport = self.cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
            return

        print(4 * "\n")
        print("Your home airport is", home_airport["name"])

        randomAirports = [self.randomAirport(), self.randomAirport(), self.randomAirport()]
        print("Choose your destination airport:")
        for i, airport in enumerate(randomAirports):
            print(f"{i + 1}. {airport['name']} ({airport['ident']})")

        choice = int(input("Choose 1-3: "))
        if choice < 1 or choice > 3:
            print("Invalid choice")
            self.new_game()
            return

        self.destination_airport = randomAirports[choice - 1]["ident"]

        try:
            self.cursor.execute(
                "INSERT INTO game_data (player_name, home_airport_ident, current_airport_ident, destination_airport_ident, total_distance) "
                "VALUES (%s, %s, %s, %s, %s)",
                (name, home_airport['ident'], self.current_airport, self.destination_airport,
                 self.total_distance))
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
            return

        self.main()

    def main(self):
        print(4*"\n")
        print("Game data:")
        print("Player name:", self.name)

        try:
            self.cursor.execute("SELECT * FROM airport WHERE ident = %s", (self.home_airport,))
            home_airport = self.cursor.fetchone()
            print("Home airport:", home_airport["name"])
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()

        try:
            self.cursor.execute("SELECT * FROM airport WHERE ident = %s", (self.current_airport,))
            current_airport = self.cursor.fetchone()
            print("Current airport:", current_airport["name"])
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()

        try:
            self.cursor.execute("SELECT * FROM airport WHERE ident = %s", (self.destination_airport,))
            destination_airport = self.cursor.fetchone()
            print("Destination airport:", destination_airport["name"])
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()

        print("Total distance:", round(self.total_distance, 1), "km")

        while self.current_airport != self.destination_airport:
            self.fly()

        self.gameWin()

    def fly(self):
        choice = input("Enter airport ident or 's' for searching closeby airports (airport can be max 1000km away): ")

        if choice == 's':
            self.getClosestAirports()
            self.fly()
            return

        print("\n\n")
        try:
            self.cursor.execute("SELECT * FROM airport WHERE ident = %s", (choice,))
            airport = self.cursor.fetchone()
            if airport is None:
                print("Invalid airport")
                self.fly()
                return
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
            return

        try:
            self.cursor.execute("SELECT * FROM airport WHERE ident = %s", (self.current_airport,))
            current_airport = self.cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
            return

        distance = haversine_distance(current_airport["latitude_deg"], current_airport["longitude_deg"],
                                      airport["latitude_deg"], airport["longitude_deg"])

        if distance > 500:
            print("Too far away")
            self.fly()
            return

        self.current_airport = airport["ident"]

        try:
            self.cursor.execute("UPDATE game_data SET current_airport_ident = %s WHERE player_name = %s",
                                (airport['ident'], self.name))
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()

        print("You have arrived to", airport["name"])
        print("Distance traveled:", round(distance, 1), "km")
        print("This flight produces", self.disntace_to_co2(distance), "grams of CO2")
        print("You have produced a total of ", self.disntace_to_co2(self.total_distance), "grams of CO2")
        self.total_distance += distance

        try:
            self.cursor.execute("UPDATE game_data SET total_distance = %s WHERE player_name = %s",
                                (self.total_distance, self.name))
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()

        print("Total distance traveled:", round(self.total_distance, 1), "km")

    def randomAirport(self):
        try:
            self.cursor.execute("SELECT * FROM airport ORDER BY RAND() LIMIT 1")
            return self.cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()
            return None

    def gameWin(self):
        print("You have arrived at your destination!")
        print(f"You produced {round(155 * self.total_distance, 0)} grams of CO2")
        print("Congratulations!")

        try:
            self.cursor.execute("DELETE FROM game_data WHERE player_name = %s", (self.name,))
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection.rollback()

        self.game_start()

    def disntace_to_co2(self, distance):
        return round(155 * distance, 0)


game = Game(user="root", password="password", database="flight_game")
game.game_start()
