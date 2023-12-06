# Distributed-Project - Period Tracker Application
To create a database to save user info, run this in your terminal. (PowerShell)
flask db init
flask db migrate
at first it gave me an error so i ran this: $env:FLASK_APP = "main"
tried flask db migrate again
then it worked
then run flask db upgrade
