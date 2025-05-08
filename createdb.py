import mysql.connector

# Connect to MySQL server as root
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="@Passw0rd123"  
)

# Create a cursor
cursor = conn.cursor()

# Create database
cursor.execute("CREATE DATABASE IF NOT EXISTS telemedicine_db")

# Create user and grant privileges (optional but recommended)
cursor.execute("CREATE USER IF NOT EXISTS 'telemedicine_user'@'localhost' IDENTIFIED BY 'your_password'")
cursor.execute("GRANT ALL PRIVILEGES ON telemedicine_db.* TO 'telemedicine_user'@'localhost'")
cursor.execute("FLUSH PRIVILEGES")

# Verify the database was created
cursor.execute("SHOW DATABASES")
for db in cursor:
    print(db)

# Close the connection
cursor.close()
conn.close()

print("Database created successfully!")