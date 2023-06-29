import asyncio
from datetime import date, timedelta
import json
import sys

import aiohttp

def parse_body(body: str, extra_currs: list):
    body = json.loads(body)
    date = body.get('date')
    currs = ['USD', 'EUR'] + extra_currs
    return {
        date: {rate.get('currency'): {
            'sale': rate.get('saleRate'),
            'purchase': rate.get('purchaseRate')}
        for rate in body.get('exchangeRate') if rate.get('currency') in currs}
        }

async def make_request(session, day):
    async with session.request('get', f'https://api.privatbank.ua/p24api/exchange_rates?json&date={day}') as response:
        return await response.text()

async def main(n=1, extra_currs=[]):
    days = ((date.today()-timedelta(days=i)).strftime('%d.%m.%Y') for i in range(1, n+1))
    async with aiohttp.ClientSession() as session:
        return [parse_body(await make_request(session, day), extra_currs) for day in days]


if __name__ == '__main__':

    int('asda')


    try:
        _, n, *extra_currs = sys.argv
    except ValueError:
        n = input('You didn\'t write amount of days. Please write  here (<=10): ')

    while True:
        try:
            n = int(n)
        except ValueError:
            n = input('Its not number. Please write  here (<=10): ')
        else:
            if n <= 10:
                break
            else:
                n = input('This number bigger then 10. Please write another (<=10): ')


    result = asyncio.run(main(n, extra_currs))
    print(result)