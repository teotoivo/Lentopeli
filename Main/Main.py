import mysql.connector

user = "root"
password = "password"
database = "flight_game"

connection = mysql.connector.connect(
        host="localhost",
        port="3306",
        user=user,
        password=password,
        database=database
    )


