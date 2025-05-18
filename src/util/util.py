from datetime import datetime


def str_to_date(date_str):
    return datetime.strptime(date_str, '%d/%m/%Y').date()

def str_to_datetime(date_str):
    return datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S')


def parse_date_format(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')


def convert_comma_to_dot(value):
    if value == '':
        return None
    try:
        return float(value.replace(',', '.'))
    except ValueError:
        return value