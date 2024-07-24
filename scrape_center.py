from flask import Flask, render_template, send_from_directory, jsonify
from bs4 import BeautifulSoup
import requests
import datetime
import csv
import os
from sys import platform
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def parse_category(src):
    logging.debug(f"Fetching category from URL: {src}")
    res = requests.get(src)
    if res.status_code != 200:
        logging.error(f"Failed to fetch URL: {src} with status code: {res.status_code}")
        return
    soup = BeautifulSoup(res.text, 'html.parser')
    products = soup.select('span[itemprop]')
    prices = soup.select('.price')
    parse_page(products, prices, src)
    return src


def parse_page(products_info, prices_info, src):
    products_with_prices = []

    for idx, item in enumerate(products_info):
        title = item.getText()
        price_float = prices_info[idx].getText().replace(' руб.', '').strip()
        ready_to_convert_price = price_float.replace(' ', '')
        if ready_to_convert_price == 'Ценууточняйте':
            continue
        else:
            floated_priced = float(ready_to_convert_price)
            products_with_prices.append({'title': title, 'fee': floated_priced})

    titles = []
    fees = []
    store_data_as_csv(values_detector(products_with_prices, titles, fees), detect_site(src), detect_category(src))
    return products_with_prices


def detect_site(src):
    site_index = src.index('.by')
    site_address = src[8:site_index + 3]
    logging.debug(f"Detected site: {site_address}")
    return site_address


def detect_category(src):
    site_index = src.index('.by')

    try:
        question_index = src.index('?')
    except ValueError:
        question_index = -1

    if question_index != -1:
        long_address = src[site_index + 4:question_index + 1]
    else:
        long_address = src[site_index + 4:-1]

    slash_index = long_address.index('/')

    category_address = long_address[slash_index + 1:-1]
    logging.debug(f"Detected category: {category_address}")
    return category_address


def values_detector(li, li2, li3):
    i = 0

    for item in li:
        keys_detector = li[i]
        title_value = keys_detector.get('title')
        li2.append(title_value)

        price_value = keys_detector.get('fee')
        li3.append(price_value)
        i += 1

    clean_data = list(zip(li2, li3))
    return clean_data


# Define the function for creating the data_scrapper folder
def create_parser_folder():
    folder_name = 'data_scrapper'
    home_dir = os.path.expanduser("~")
    folder = os.path.join(home_dir, folder_name)
    logging.debug(f"Creating directory at path: {folder}")
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


# Define the function to store data as a CSV
def store_data_as_csv(zip_obj, site, category, directory_path=None):
    if directory_path is None:
        directory_path = create_parser_folder()
    date_today = datetime.datetime.now()
    today = date_today.strftime('%Y-%m-%d')
    os.makedirs(directory_path, exist_ok=True)
    file_path = os.path.join(directory_path, f'{site}-{category}-{today}.csv')
    logging.debug(f"Saving CSV file at path: {file_path}")
    try:
        with open(file_path, 'w+', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Наименование товара', 'Цена, руб.'])
            for item in zip_obj:
                writer.writerow(item)
        logging.info(f"CSV file saved successfully at {file_path}")
    except Exception as e:
        logging.error(f"Failed to save CSV file: {e}")
    return file_path


def check_os(path):
    os.makedirs(path, exist_ok=True)


# Define the function to trigger CSV generation
@app.route('/trigger-csv-generation')
def trigger_csv_generation():
    zip_obj = [('Item1', 100), ('Item2', 200)]  # Example data
    site = 'example_site'
    category = 'example_category'
    file_path = store_data_as_csv(zip_obj, site, category)
    directory, filename = os.path.split(file_path)
    return render_template('parser.html', html_data='Your Source URL Here', csv_filename=filename)


# Define the function to download the CSV file
@app.route('/download-csv/<path:filename>', methods=['GET'])
def download_csv(filename):
    directory_path = create_parser_folder()
    try:
        return send_from_directory(directory_path, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


if __name__ == '__main__':
    app.run(debug=True)
