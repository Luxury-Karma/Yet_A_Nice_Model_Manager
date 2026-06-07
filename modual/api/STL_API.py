"""
@File: STL_API.py
@Project: modual\api\STL_API
@Author: Alexandre Gauvin
This file is holding all API request link to getting or adding STLs.
"""
from flask import request, Flask, jsonify

app = Flask(__name__)  # TODO: unify all of them inside of main
@app.route('/test', methods=['GET'])
def test():
    return jsonify({'data': 'It is working!'})

@app.route('/get_stl', methods=['GET'])
def get_stl_list():
    """
    Get the list of all STL from the SQL database
    :return: list of STL
    """
    pass

@app.route('/add_stl', methods=['POST'])
def add_stl():
    """
    Add a STL file or directory to the SQL database
    :return:
    """
    return

@app.route('/find_stl', methods=['GET'])
def find_all_stl():
    """
    Find all STL files in the system and add it to the SQL database
    :return:
    """
    return



if __name__ == '__main__':
    app.run(debug=True)