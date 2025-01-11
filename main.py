import random
import asyncio
import aiohttp
import threading
import os
from itertools import islice

def generate_codes_batch(size):
    return [''.join(random.choices("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=16)) for _ in range(size)]

async def check_code(session, code: str) -> tuple[str, bool]:
    try:
        async with session.get(
            f"https://discord.com/api/v10/entitlements/gift-codes/{code}?with_application=false&with_subscription_plan=true",
            timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
            return code, 200 <= response.status <= 204
    except:
        return code, False

async def check_batch_codes():
    codes_pool = generate_codes_batch(16)
    async with aiohttp.ClientSession(headers={
            "authority": "discord.com",
            "method": "GET",
            "scheme": "https",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Cookie": "",
            "Pragma": "no-cache",
            "Priority": "u=0, i",
            "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        }, connector=aiohttp.TCPConnector(limit=0)) as session:
        while codes_pool:
            batch = list(islice(codes_pool, 500))
            if not batch:
                codes_pool = generate_codes_batch(16)
                continue

            tasks = [check_code(session, code) for code in batch]
            for result in await asyncio.gather(*tasks, return_exceptions=True):
                if isinstance(result, tuple):
                    code, is_valid = result
                    if is_valid:
                        print(f"\033[92mValid code: {code}\033[0m")
                        with open('valid_codes.txt', 'a') as f:
                            f.write(f"{code}\n")
                    else:
                        print(f"\033[91mInvalid code: {code}\033[0m", end="\r")

def thread_worker():
    while True:
        asyncio.run(check_batch_codes())

threads = []
for _ in range(min(8, os.cpu_count())):
    thread = threading.Thread(target=thread_worker)
    thread.daemon = True
    threads.append(thread)
    thread.start()
while True:
    threading.Event().wait()