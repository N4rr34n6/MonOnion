# MonOnion.py

MonOnion.py is an advanced tool for monitoring `.onion` domains, offering unique functionalities for tracking changes in content, links, and service status. With the ability to send notifications via Telegram, it allows you to detect modifications on websites and observe patterns of behavior across hidden services.

## Features

- **Continuous Onion Domain Monitoring:** MonOnion.py automatically checks the status and content of multiple `.onion` sites, alerting you to any significant changes.

- **Content Change Detection:** If the page content changes, the system sends a notification with details of the modification. It also tracks added or removed links within the monitored pages.

- **Telegram Notifications:** Changes in domain status and content are automatically sent to a configured Telegram channel, including attachments such as screenshots or CURL responses of the site.

- **Screenshot Capturing:** If changes are detected, the script generates a screenshot and sends it to the designated Telegram channel.

- **Service Status Tracking:** MonOnion.py detects when a service goes offline or comes back online, helping determine if multiple domains might be hosted on the same server by observing patterns of service stops, starts, or restarts.

- **Content and Link History:** It saves records of previous links and content for future comparisons, making it easy to detect any alterations on the page.

## Use Cases

1. **Dark Web Monitoring:** Useful for researchers, journalists, and analysts who want to keep track of hidden sites on the Tor network.

2. **Server Pattern Detection:** By observing changes in the status of multiple `.onion` domains, MonOnion.py can help identify whether a group of sites is hosted on the same server by analyzing downtime and restarts.

3. **Threat Analysis:** MonOnion.py can be used as a tool to detect suspicious activity or sudden changes on Dark Web pages, facilitating a quick response to potential threats.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/n4rr34n6/MonOnion.py.git
   cd MonOnion.py
   ```

2. Install the required dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Configure your `config.json` file with your `.onion` domains and Telegram credentials.

4. Run the script:
   ```bash
   python3 MonOnion.py
   ```

## Configuration

The `config.json` file should contain your Telegram connection details and the domains you wish to monitor. Here's a basic example:

```json
{
    "api_id": 123456,
    "api_hash": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "phone": "+1234567890",
    "channel_id": -1000000000000,
    "pages": [
        {
            "url": "http://example1.onion/",
            "previous_links_path": "previous_links.txt",
            "current_links_path": "current_links.txt",
            "previous_content_path": "previous_content.txt",
            "screenshot_path": "screenshot.jpg",
            "curl_response_path": "curl_response.txt",
            "status_file_path": "status.txt"
        }
    ]
}
```

## Dependencies

- **Python 3.x**
- **Telethon** (for Telegram notifications)
- **requests** (for fetching page content)
- **wkhtmltoimage** (for screenshot capturing)

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the [LICENSE](LICENSE) file for more details.
