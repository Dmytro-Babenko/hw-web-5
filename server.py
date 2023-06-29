import asyncio
import aiofile
import aiopath
import logging
import json
from datetime import date, timedelta
import websockets
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
import aiohttp



logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    def parse_body(self, body: str, extra_currs: list):
        body = json.loads(body)
        date = body.get('date')
        currs = ['USD', 'EUR'] + extra_currs
        return {
            date: {rate.get('currency'): {
                'sale': rate.get('saleRate'),
                'purchase': rate.get('purchaseRate')}
            for rate in body.get('exchangeRate') if rate.get('currency') in currs}
            }

    async def make_request(self, session, day):
        async with session.request('get', f'https://api.privatbank.ua/p24api/exchange_rates?json&date={day}') as response:
            return await response.text()

    async def get_exchange(self, n=1, extra_currs=[]):
        days = ((date.today()-timedelta(days=i)).strftime('%d.%m.%Y') for i in range(1, n+1))
        async with aiohttp.ClientSession() as session:
            return [self.parse_body(await self.make_request(session, day), extra_currs) for day in days]

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            message:str
            if message.lower().startswith('exchange'):
                try:
                    _, n, *extra_currs = message.split(' ')
                    n = int(n)
                except ValueError:
                    message = 'You didn\'t write amount of days. Please write it (<=10)'
                else:
                    if n <= 10:
                        message = json.dumps(await self.get_exchange(n, extra_currs))
                    else:
                        message = 'This number bigger then 10. Please write another (<=10)'
                await self.log_exchange('log.txt', message)
            await self.send_to_clients(message)

    async def log_exchange(self, path, message):
        if await aiopath.Path(path).exists():
            async with aiofile.async_open(path, 'a') as fh:
                await fh.write(f'{message}\n')
        else:
            async with aiofile.async_open(path, 'w') as fh:
                await fh.write(f'{message}\n')


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 4001):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())