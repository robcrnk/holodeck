import paramiko
import mariadb
import requests
import os
from datetime import datetime, timedelta

# Configuration des serveurs
servers = [
    {"hostname": "192.168.57.131", "username": "monitor", "password": "123"},  # MariaDB
    {"hostname": "192.168.57.130", "username": "monitor", "password": "123"},  # WebServer
    {"hostname": "192.168.57.129", "username": "monitor", "password": "123"}   # SFTPServer
]

# Configuration de la base de données
db_config = {
    "host": "192.168.57.131",
    "user": "bdduser",
    "password": "123",
    "database": "bdd"
}

# Webhook URL for Google Chat (Remplacez par votre URL de webhook réelle)
WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/AAAA9EnlEK0/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=lcbmnV2FACoCSjiaRpN2eoekEmlaY9ms8D9XL97cOZk"

# Connexion à la base de données
try:
    db = mariadb.connect(**db_config)
    cursor = db.cursor()
    print("Connexion à MariaDB réussie")

    # Création de la table si elle n'existe pas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sys_res (
        id INT AUTO_INCREMENT PRIMARY KEY,
        server VARCHAR(255),
        timestamp DATETIME,
        cpu_usage FLOAT,
        ram_usage FLOAT,
        disk_usage FLOAT
    )
    """)
    print("Table sys_res vérifiée/créée")
except mariadb.Error as e:
    print(f"Erreur de connexion à MariaDB : {e}")
    exit(1)

# Fonction pour récupérer l'état des ressources système
def get_system_resources(server):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server["hostname"], username=server["username"], password=server["password"])
        print(f"Connexion SSH réussie à {server['hostname']}")

        # Récupération de l'utilisation du CPU
        stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)'")
        cpu_output = stdout.read().decode()
        print(f"CPU output pour {server['hostname']} : {cpu_output}")
        cpu_usage = float(cpu_output.split()[1].replace(',', '.'))

        # Récupération de l'utilisation de la RAM
        stdin, stdout, stderr = ssh.exec_command("free -m | grep 'Mem'")
        ram_output = stdout.read().decode()
        print(f"RAM output pour {server['hostname']} : {ram_output}")
        mem_info = ram_output.split()
        ram_usage = float(mem_info[2].replace(',', '.')) / float(mem_info[1].replace(',', '.')) * 100

        # Récupération de l'utilisation du disque
        stdin, stdout, stderr = ssh.exec_command("df -h | grep '/dev/sda1'")
        disk_output = stdout.read().decode()
        print(f"Disk output pour {server['hostname']} : {disk_output}")
        disk_usage = float(disk_output.split()[4].replace('%', '').replace(',', '.'))

        ssh.close()
        return cpu_usage, ram_usage, disk_usage
    except Exception as e:
        print(f"Erreur lors de la récupération des ressources système depuis {server['hostname']} : {e}")
        return None, None, None

# Fonction pour insérer les données dans la base de données
def insert_data(server, cpu_usage, ram_usage, disk_usage):
    if cpu_usage is not None and ram_usage is not None and disk_usage is not None:
        timestamp = datetime.now()
        cursor.execute("""
        INSERT INTO sys_res (server, timestamp, cpu_usage, ram_usage, disk_usage)
        VALUES (%s, %s, %s, %s, %s)
        """, (server["hostname"], timestamp, cpu_usage, ram_usage, disk_usage))
        db.commit()
        print(f"Données insérées pour {server['hostname']} : CPU={cpu_usage}, RAM={ram_usage}, DISK={disk_usage}")

# Fonction pour supprimer les données de plus de 72 heures
def delete_old_data():
    cutoff = datetime.now() - timedelta(hours=72)
    cursor.execute("DELETE FROM sys_res WHERE timestamp < %s", (cutoff,))
    db.commit()
    print("Données de plus de 72 heures supprimées")

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

# Vérifier les états des serveurs et récupérer les ressources système
def monitor_servers():
    message = "État des serveurs et ressources système:\n"
    for server in servers:
        # Vérification de l'état du serveur
        server_status = check_server(server["hostname"], 3306 if server["hostname"] == "192.168.57.131" else 80 if server["hostname"] == "192.168.57.130" else 22)
        
        if server_status:
            message += f"✅ {server['hostname']} est en ligne.\n"
            # Récupérer les ressources système
            cpu_usage, ram_usage, disk_usage = get_system_resources(server)
            if cpu_usage is not None and ram_usage is not None and disk_usage is not None:
                message += f"   - Utilisation CPU: {cpu_usage:.2f}%\n"
                message += f"   - Utilisation RAM: {ram_usage:.2f}%\n"
                message += f"   - Utilisation Disque: {disk_usage:.2f}%\n"
        else:
            message += f"❌ {server['hostname']} est hors ligne.\n"
    
    return message

# Exécution principale
if __name__ == "__main__":
    # Vérifier les états des serveurs et récupérer les ressources système
    server_status_message = monitor_servers()
    
    # Envoyer le message de statut des serveurs à Google Chat
    send_message(server_status_message)
    
    # Insertion des données pour chaque serveur
    for server in servers:
        cpu_usage, ram_usage, disk_usage = get_system_resources(server)
        insert_data(server, cpu_usage, ram_usage, disk_usage)

    # Suppression des anciennes données
    delete_old_data()

    # Fermeture de la connexion à la base de données
    cursor.close()
    db.close()
    print("Connexion à la base de données fermée")
