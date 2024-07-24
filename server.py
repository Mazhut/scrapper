from flask import Flask, render_template, request, redirect
from scrape_center import parse_category

app = Flask(__name__)


@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/parser.html', methods=['GET', 'POST'])
def parse_data():
    link = request.form['enter_value']
    parse_category(link)
    return render_template('parser.html', html_data=link)
