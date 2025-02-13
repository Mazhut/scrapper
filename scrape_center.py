from flask import Flask, send_from_directory, send_file
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
            products_with_prices.append({'title': title,  'fee': floated_priced})

    titles = []
    fees = []
    store_data_as_csv(values_detector(products_with_prices, titles, fees), detect_site(src), detect_category(src))
    return products_with_prices


def detect_site(src):
    site_index = src.index('.by')
    site_address = src[8:site_index+3]
    logging.debug(f"Detected site: {site_address}")
    return site_address


def detect_category(src):
    site_index = src.index('.by')

    try:
        question_index = src.index('?')
    except ValueError:
        question_index = -1

    if question_index != -1:
        long_address = src[site_index+4:question_index+1]
    else:
        long_address = src[site_index+4:-1]

    slash_index = long_address.index('/')

    category_address = long_address[slash_index+1:-1]
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


def create_parser_folder():
    folder_name = 'data_scrapper'
    home_dir = os.path.expanduser("~")
    folder = os.path.join(home_dir, folder_name)

    logging.debug(f"Creating directory at path: {folder}")

    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def store_data_as_csv(zip_obj, site, category, directory_path=None):
    if directory_path is None:
        directory_path = create_parser_folder()

    date_today = datetime.datetime.now()
    str_today = str(date_today)
    today = str_today.split()[0]

    os.makedirs(directory_path, exist_ok=True)

    file_path = os.path.join(directory_path, f'{site}-{category}-{today}.csv')
    csv_name = f'{site}-{category}-{today}.csv'
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

    download_csv(site, category, today, csv_name)

    return file_path


def check_os(path):
    os.makedirs(path, exist_ok=True)


@app.route('/getCSV')
def download_csv(li1, li2, actual_date, file_name):
    return send_file(
        f'/opt/render/data_scrapper/{file_name}',
        mimetype='text/csv',
        download_name=f'{li1}-{li2}-{actual_date}.csv',
        as_attachment=True
    )


if __name__ == '__main__':
    app.run(debug=True)
