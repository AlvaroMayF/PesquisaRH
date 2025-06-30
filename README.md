Organizational Climate Survey System - Rede Hospitalar Samar
This repository contains the source code for the web application developed to automate the collection, processing, and analysis of the Organizational Climate Survey at Rede Hospitalar Samar.

Project Status: Version 1.0 - In Production

📜 About the Project
The Organizational Climate Survey System is a strategic tool aimed at replacing manual processes, ensuring the total anonymity of employees, and providing management with structured and visual data to support decision-making.

Check out the full interactive documentation: Click here to see the system presentation
(Note: Replace the placeholders above after hosting the HTML presentation with GitHub Pages)

✨ Key Features (v1.0)
The system is divided into two main user flows:

👤 Employee Flow
Secure Authentication: Login via CPF (Brazilian individual taxpayer registry) and Date of Birth.

Access Validation: Allows access only to registered employees who have not yet responded.

Dynamic Form: Questions are loaded directly from the database.

Anonymity Guaranteed: Responses are saved without any link to the employee's identity.

ադ Administrator Flow
Analytics Dashboard: A panel showing the real-time participation rate and aggregated results.

Data Visualization: Interactive charts (pie, bar) for quantitative analysis.

Qualitative Analysis: Anonymous listing of open-text responses.

Employee Management (CRUD): A complete interface to add, edit, and deactivate participants.

🚀 Technologies Used
Backend: Python 3 with Flask

Frontend: HTML5, CSS3 (with Tailwind CSS), JavaScript

Database: MySQL

Virtual Environment: venv

Dependencies: (Listed in requirements.txt)

⚙️ How to Run the Project Locally
Follow the steps below to set up and run the project on your machine.

Prerequisites
Python 3.x installed

Git installed

A running MySQL database server

1. Clone the Repository
git clone https://github.com/[YOUR-GITHUB-USERNAME]/[REPOSITORY-NAME].git
cd [REPOSITORY-NAME]

2. Set Up the Virtual Environment
It is good practice to use a virtual environment to isolate project dependencies.

# Create the virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

3. Install Dependencies
With the virtual environment activated, install all necessary libraries.

pip install -r requirements.txt

(Note: Make sure you have a requirements.txt file with all dependencies, such as Flask, mysql-connector-python, etc.)

4. Configure the Database
Create a database on your MySQL server (e.g., pesquisa_rh).

Import the table structure (you can use an SQL dump script from your development database).

Set up the environment variables. Create a .env file in the project root with your credentials:

DB_HOST=localhost
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=pesquisa_rh

5. Run the Application
Execute the command below to start the Flask development server.

flask run

The application will be available at http://127.0.0.1:5000 (or the address shown in your terminal).

🤝 Contributions
This project is currently under active development. To contribute, please create a new branch, make your changes, and open a Pull Request for review.

📄 License
This project is the property of Rede Hospitalar Samar. All rights reserved.git add README.md