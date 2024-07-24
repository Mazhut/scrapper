from bs4 import BeautifulSoup
import requests
import datetime
import csv

print('Paste the link that needs to be parsed below:')
link_to_parse = input()


def parse_category(src):
    res = requests.get(src)  # Making a request to the link
    soup = BeautifulSoup(res.text, 'html.parser')
    products = soup.select('span[itemprop]')
    prices = soup.select('.price')
    parse_page(products, prices, link_to_parse)
    return link_to_parse


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
    return site_address


def detect_category(src):
    site_index = src.index('.by')

    try:
        question_index = src.index('?')
    # If link does not contain '?'
    except ValueError:
        question_index = -1

    if question_index != -1:
        long_address = src[site_index+4:question_index+1]
    else:
        long_address = src[site_index+4:-1]

    slash_index = long_address.index('/')

    category_address = long_address[slash_index+1:-1]
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


def store_data_as_csv(zip_obj, site, category):
    date_today = datetime.datetime.now()
    str_today = str(date_today)
    today = str_today.rsplit()[0]

    with open(f'{site}-{category}-{today}.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Наименование товара', 'Цена, руб.'])
        for item in zip_obj:
            writer.writerow(item)


parse_category(link_to_parse)
