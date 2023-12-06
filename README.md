# Distributed-Project - Period Tracker Application
To create a database to save user info, run this in your terminal. (PowerShell)
1. flask db init
2. flask db migrate
3. at first it gave me an error so i ran this: $env:FLASK_APP = "main"
4. tried flask db migrate again
5. then it worked
6. then run flask db upgrade
