# Distributed-Project - Period Tracker Application

*How* *To* *Compile*
A. Ensure you have every library on main.py installed in your venv. Use pip
   
B. Ensure your database has been initialized
  To create a database to save user info, run this in your terminal. (PowerShell):
  1. flask db init
  2. flask db migrate
  3. at first it gave me an error so i ran this: $env:FLASK_APP = "main"
  4. tried flask db migrate again
  5. then it worked
  6. then run flask db upgrade
  
  This would then create a new instance and migration folder, you have to delete the one we have on the repo first (assuming you have it downloaded). 
  To use the one on the repo, run the same code, if it doesn't work, create a new one instead
  
C. Run main.py, Flask would provide a link: http://127.0.0.1:5000/. Click on the link and interact with the application.
