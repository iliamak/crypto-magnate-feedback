# Запустить один раз: python get_token.py
# Откроет ссылку для авторизации, после редиректа вставить code
import requests
import webbrowser
import urllib.parse

CLIENT_ID = input("Client ID: ")
CLIENT_SECRET = input("Client Secret: ")
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

url = (
    f"https://app.asana.com/-/oauth_authorize"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&response_type=code"
)
webbrowser.open(url)
code = input("Вставь code из браузера: ")

resp = requests.post("https://app.asana.com/-/oauth_token", data={
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "code": code,
})
data = resp.json()
print("\nRESULT:")
print("REFRESH_TOKEN:", data.get("refresh_token"))
print("ACCESS_TOKEN:", data.get("access_token"))
if "error" in data:
    print("ERROR:", data)
