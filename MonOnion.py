import os
import re
import time
import getpass
import requests
import json
import asyncio
import socks
import subprocess
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import FloodWaitError, SessionPasswordNeededError
import chardet

# Load configuration from JSON file
def load_config(config_path='config.json'):
    with open(config_path, 'r', encoding='utf-8') as file:
        return json.load(file)

config = load_config()

api_id = config['api_id']
api_hash = config['api_hash']
phone = config['phone']
channel_id = config['channel_id']
pages = config['pages']

# Create Telegram client
client = TelegramClient('session_name', api_id, api_hash)

# Function to connect to Telegram
async def connect_to_telegram():
    while True:
        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone)
                code = input('Enter Telegram code: ')
                try:
                    await client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    password = getpass.getpass('Enter Telegram session password: ')
                    await client.sign_in(password=password)
            break
        except (ConnectionError, FloodWaitError) as e:
            print(f"Connection error: {e}. Retrying in 60 seconds...")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 60 seconds...")
            await asyncio.sleep(60)

# Function to send a notification to Telegram
async def send_notification(message):
    retries = 5
    while retries > 0:
        try:
            entity = await client.get_entity(channel_id)
            await client.send_message(entity, message, parse_mode='html')
            break
        except Exception as e:
            print(f"Connection error while sending notification: {e}. Retrying in 60 seconds...")
            await asyncio.sleep(60)
            retries -= 1
            await connect_to_telegram()
    if retries == 0:
        print("Failed to send the notification after several attempts.")

# Function to get the page content with encoding detection
def get_page_content(url):
    try:
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        response = requests.get(url, proxies=proxies)

        # Detect encoding
        result = chardet.detect(response.content)
        encoding = result['encoding']

        if encoding:
            content = response.content.decode(encoding)
        else:
            content = response.text

        return response.status_code, content
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving page content: {e}")
        return None, ""

# Function to extract links from the page content
def extract_links(content):
    return set(re.findall(r'(https?://[^\s]+)', content))

# Function to capture a screenshot of a URL
def capture_screenshot(url, output_path):
    try:
        subprocess.run(['torsocks', 'wkhtmltoimage', url, output_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error capturing screenshot: {e}")
        return False
    return True

# Function to process each page
async def process_page(page):
    url = page["url"]
    status_file_path = page["status_file_path"]
    status_only = page.get("status_only", False)

    try:
        status_code, current_content = get_page_content(url)

        # Read the previous site status
        if os.path.exists(status_file_path):
            with open(status_file_path, 'r', encoding='utf-8') as file:
                previous_status = file.read().strip()
        else:
            previous_status = "unknown"

        current_status = "available" if status_code == 200 else "unavailable"

        # Save the current site status
        with open(status_file_path, 'w', encoding='utf-8') as file:
            file.write(current_status)

        if current_status == "unavailable":
            if previous_status != "unavailable":
                message = f"The site {url} is unavailable. HTTP status code: {status_code}."
                await send_notification(message)
            return
        elif current_status == "available" and previous_status == "unavailable":
            message = f"The site {url} is back online. HTTP status code: {status_code}."
            await send_notification(message)

        # If only status checking is required, exit the function here
        if status_only:
            return

        previous_links_path = page["previous_links_path"]
        current_links_path = page["current_links_path"]
        previous_content_path = page["previous_content_path"]
        screenshot_path = page["screenshot_path"]
        curl_response_path = page["curl_response_path"]

        # Read previous links
        if os.path.exists(previous_links_path):
            with open(previous_links_path, 'r', encoding='utf-8') as file:
                previous_links = set(file.read().splitlines())
        else:
            previous_links = set()

        # Read previous content
        if os.path.exists(previous_content_path):
            with open(previous_content_path, 'r', encoding='utf-8') as file:
                previous_content = file.read()
        else:
            previous_content = ''

        # Save and send curl response content only if it has changed
        if current_content != previous_content:
            with open(curl_response_path, 'w', encoding='utf-8') as f:
                f.write(current_content)
            if os.path.getsize(curl_response_path) > 0:
                retries = 5
                while retries > 0:
                    try:
                        entity = await client.get_entity(channel_id)
                        await client.send_file(entity, curl_response_path)
                        break
                    except Exception as e:
                        print(f"Connection error while sending file: {e}. Retrying in 60 seconds...")
                        await asyncio.sleep(60)
                        retries -= 1
                        await connect_to_telegram()
                if retries == 0:
                    print("Failed to send the file after several attempts.")
            else:
                print(f"The file {curl_response_path} is empty and will not be sent.")
            os.remove(curl_response_path)

            # Update previous content
            previous_content = current_content
            with open(previous_content_path, 'w', encoding='utf-8') as file:
                file.write(previous_content)

            message = f"Changes detected in the content of the page {url}.\nHTTP status code: {status_code}."
            await send_notification(message)

        current_links = extract_links(current_content)

        # Read currently saved links
        if os.path.exists(current_links_path):
            with open(current_links_path, 'r', encoding='utf-8') as file:
                saved_links = set(file.read().splitlines())
        else:
            saved_links = set()

        # Determine added and removed links
        added_links = current_links - saved_links
        removed_links = saved_links - current_links

        # If there are changes in links, update files and send a notification
        if added_links or removed_links:
            with open(current_links_path, 'w', encoding='utf-8') as file:
                file.write('\n'.join(current_links))
            with open(previous_links_path, 'w', encoding='utf-8') as file:
                file.write('\n'.join(current_links))

            added_links_str = '\n'.join(f"<a href='{link}'>{link}</a>" for link in added_links)
            removed_links_str = '\n'.join(f"<a href='{link}'>{link}</a>" for link in removed_links)

            message = (
                f"<b>Changes detected in the links of the page {url}:</b>\n\n"
                f"<u>Added links:</u>\n{added_links_str}\n\n"
                f"<u>Removed links:</u>\n{removed_links_str}\n\n"
                f"HTTP status code: {status_code}."
            )
            await send_notification(message)

            # Capture and send screenshot
            if capture_screenshot(url, screenshot_path):
                retries = 5
                while retries > 0:
                    try:
                        entity = await client.get_entity(channel_id)
                        await client.send_file(entity, screenshot_path)
                        break
                    except Exception as e:
                        print(f"Connection error while sending screenshot: {e}. Retrying in 60 seconds...")
                        await asyncio.sleep(60)
                        retries -= 1
                        await connect_to_telegram()
                if retries == 0:
                    print("Failed to send the screenshot after several attempts.")
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
            else:
                print(f"Failed to capture the screenshot of the page {url}.")

        print(f"No changes detected in the links of the page {url}.")

    except Exception as e:
        print(f"Error processing the page {url}: {e}")
        await asyncio.sleep(60)  # Wait 60 seconds before retrying in case of error

# Main function with infinite loop
async def main():
    await connect_to_telegram()
    while True:
        tasks = [process_page(page) for page in pages]
        await asyncio.gather(*tasks)
        # Wait before the next execution
        await asyncio.sleep(30)  # Wait 30 seconds before checking the pages again

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
