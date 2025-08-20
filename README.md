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
- Open app.py
- In the top right corner, next to the 'Play' button, click Run Shiny App
- This will open the app in VS Code’s browser preview. Copy the URL and paste it into your regular browser for best results (the app is designed for fullscreen mode)



## App description
### User selection screen
After startup, the app opens the user selection screen. Here you have two options:
- Select the tile with your user name to load your previously created profile
- Create a new profile by entering your name and clicking Create
Both actions will automatically lead to the home screen

### Home screen
The home screen shows the user’s habits ordered by due date:
- The upper container shows the habits that need to be checked today to continue their streak
- Optional habits have a valid streak ongoing, but don’t need to be completed today (e.g., a habit with a weekly period where the last check date is less than a week ago)
- Broken habits are overdue and currently don’t have an ongoing streak. Completing them today will reset them, and they will appear the next day as either due or optional, depending on their period
On the home screen, there are also two buttons that lead to either the Edit Habits or Analyze Habits screen

### Edit Habits screen
On this screen, the user can edit their habits:
- To add a new habit, enter a name and select a period (choosing a custom period will open a field to enter the number of days). After completion, click Save Changes
- To edit a habit, click on the habit in the table on the left. The fields will be filled with the habit’s information. Change either the name or the period and click Save Changes to update the habit in the database
- The status field allows you to archive habits instead of deleting them. Select a habit from the table, change its status to Archived, and click Save Changes to update the database
- To delete a habit, select it in the table and click Delete. The habit will be permanently removed from the database
- To delete the current user and all their habits, click Delete User
Click Back to return to the home screen

### Analyze Habits screen
On this screen, the user receives an overview of the streaks of their habits. On the right side of the UI, it is possible to download different CSVs with the data for further analysis in another tool.
The plot only shows habits that have received at least one check, and the maximum time span displayed is currently limited to 180 days.

The buttons on the right side will only be active when there is data to download:
- Active habits: table of all active habits
- Habits with the same periodicity: download habits by a selected period
- Archived habits: all habits that are currently archived
- Completions: number of checks for each habit
- Longest overall: the habit with the highest streak, including both active and archived habits
- Longest habit: the highest streak for a selected habit
Click Back to return to the home screen

## App folder structure
### modules
Contains one script for each page of the app

### models
Contains the user and habit classes and their methods

### services
Contains the script for the database setup and its methods. The database itself will be created here as well. state.py provides helper functions to change the reactive values in the app (current_user, current_page, and refresh_user)

### static
Contains the stylesheet and any images used in the app

### tests
Contains two scripts with test functions to verify the most important functions of the app:
- test_analytics.py: tests all functions within the analytical screen
- test_streaks.py: tests all functions related to streak calculation

### other
- app.py: the main starting script
- requirements.txt: lists the libraries used and their versions
- config.py: handles the path to the database
