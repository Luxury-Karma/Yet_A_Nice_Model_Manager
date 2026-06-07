"""
@File: webserver.py
@Project: modual\webserver.py
@Author: Alexandre Gauvin
This file is holding the web interface for the user
"""
# TODO: Here will be all of the API call from the webUI
from flask import Flask, render_template, request
app = Flask(__name__)  # TODO: unify all of them inside of main


@app.route('/', methods=['GET'])
def home_page():
    """
    Render the home page for the user
    :return: the home page
    """
    return render_template('UI/home_page.tsx')

@app.route('/login', methods='GET')
def login_page():
    """
    Render the login page for the user
    :return: render the login page
    """
    return render_template('UI/login_page.tsx')

if __name__ == '__main__':
    app.run(debug=True)
