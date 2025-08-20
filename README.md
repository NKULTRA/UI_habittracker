# UI_habittracker
A habit tracker in python shiny for the project of the course DLBDSOOFPP01 - Object Oriented and Functional Programming with Python

## Prerequisites
- Python **3.10+**
- Git (optional, for cloning)

## Installation Guide
### Option A — Clone with Git
- git clone https://github.com/NKULTRA/UI_habittracker.git
- cd UI_habittracker

### Option B — Download ZIP
1. On GitHub, click Code → Download ZIP
2. Unzip the archive
3. Open a terminal and cd into the project folder

## Create a virtual environment & install requirements.txt
### on Windows
- py -m venv .venv
- .\.venv\Scripts\activate
- py -m pip install -r requirements.txt

## Run the app
### Option A — In Terminal or cmd
- python -m shiny run --reload app.py

### Option B — In VS Code
- open app.R
- upper right corner next to the 'Play'- Button -> Run Shiny App
- this will open a browser in VS Code, copy the URL and paste it into your browser of choice, the app is only adapted to a normal browser in fullscreen - mode



## App description
### User selection screen
After startup the app opens the user selection screen, here are two options:
- select the tile with your user name to load your previously created profile
- create a new profile through entering your name and click on 'Create'
Both actions will automatically lead to the homescreen.

### Home screen
The homescreen shows the users' habits ordered regarding their due date
- the upper container shows the habits which need to be checked today to continue their streak
- optional habits are habits which have a valid streak ongoing, but to continue their streak they must not be completed today (e.g. a habit with a weekly period and its last check date is not yet a week ago)
- broken habits are over-due and currently don't have an ongoing streak, completing them today will reset them and they will show the next day in either due or optional, depending on their period

- on the home screen are two buttons which lead to either the 'edit habits' or the 'analyze habits' screen

### Edit Habits screen
On this screen the user can edit his / her habits
- to add a new habit, just enter a name for the habit and select a period (custom period selection will lead to a new field to enter the number of days its period should be); after completion click on 'Save Changes'
- to edit a habit, click on the particular habit within the table on the left, this will lead that the fields will be filled with the habits info; just change either the name or the period and click 'Save Changes' to override this habit within the database
- the status field gives the opportunity to archive habits instead of deletion, just select one habit from the table and change its status to 'Archived'; Click 'Save Changes' to change this info the database
- to delete a habit, select the habit in the table with a mouse - click and click on 'Delete'; the habit will be removed from the database permanently
- to delete the current user and all his / her habits, just click 'Delete User'
- Click 'Back' to go back to the homescreen

### Analyze Habits screen
On this screen the user receives an overview over the streaks of his / her habits, on the right side of the UI it is possible to download different CSV's with the data, to possibly analyze them in another tool
- the plot only shows habits which at least received one check in their lifetime, also the maximum number of days the plot will go back is currently set to 180
- Buttons on the right side will only be active when there is data to download:
    - Active habits gives the table of all active habits
    - Habits with the same periodicity can be downloaded, select the period of choice on the right
    - Archived habits gives all habits which are currently archived
    - Completions gives the number of checks for each habit
    - the longest overall gives the habit with the highest streak, both from active and archived habits
    - the longest habit gives the highest streak for a selected habit, select the habit of choice on the right

## App folder structure
### modules
Contains one script for each of the pages of the app

### models
contains the user and the habit class and their methods

### services
contains the script for the database setup and its methods, the database itself will be written here as well; state.py gives the small helper function to change the reactive values in the app (current_user, current_page and refresh_user)

### static
contains the stylesheet and any images which were used in the app

### tests
contains two scripts with test-functions, to test the most important functions from the app
- test_analytics.py tests all functions within the analytical screen
- test_streaks.py tests all functions linked to the streak calculation

### other
- app.py is the main starting script
- requirements.txt gives the used libraries and their versions
