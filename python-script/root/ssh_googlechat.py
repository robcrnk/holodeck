import requests
import os

# Webhook URL for Google Chat (Remplacez par votre URL de webhook réelle)
WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/AAAA9EnlEK0/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=lcbmnV2FACoCSjiaRpN2eoekEmlaY9ms8D9XL97cOZk"
# Serveur IPs
servers = {
    'MariaDB': '192.168.57.131',
    'WebServer': '192.168.57.130',
    'SFTPServer': '192.168.57.129'
}

# Commandes pour vérifier les serveurs
def check_server(ip, port):
    response = os.system(f"nc -zv {ip} {port} > /dev/null 2>&1")
    return response == 0

# Envoyer un message dans Google Chat
def send_message(message):
    headers = {'Content-Type': 'application/json'}
    data = {
        "text": message
    }
    response = requests.post(WEBHOOK_URL, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Message sent successfully: {message}")
    else:
        print(f"Failed to send message. Status Code: {response.status_code}")

# Vérifier les états des serveurs
def monitor_servers():
    message = "État des serveurs:\n"
    # Vérifier MariaDB (port 3306)
    if check_server(servers['MariaDB'], 3306):
        message += "✅ MariaDB est en ligne.\n"
    else:
        message += "❌ MariaDB est hors ligne.\n"

    # Vérifier le serveur Web (port 80)
    if check_server(servers['WebServer'], 80):
        message += "✅ Le serveur Web est en ligne.\n"
    else:
        message += "❌ Le serveur Web est hors ligne.\n"

    # Vérifier SFTP (port 22)
    if check_server(servers['SFTPServer'], 22):
        message += "✅ SFTP est en ligne.\n"
    else:
        message += "❌ SFTP est hors ligne.\n"

    # Envoyer le message à Google Chat
    send_message(message)

# Exécution principale (sans boucle infinie)
if __name__ == "__main__":
    monitor_servers()
