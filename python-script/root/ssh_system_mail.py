#!/usr/bin/env python3
import paramiko
import mariadb
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuration des seuils
CPU_THRESHOLD = 70
RAM_THRESHOLD = 80	
DISK_THRESHOLD = 75

# Configuration de l'email
ADMIN_EMAIL = "robin.mahu@laplateforme.io"
SENDER_EMAIL = "testmail621313@gmail.com"
SENDER_PASSWORD = "xqod bajt bryx edzj"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Configuration des serveurs
servers = [
    {"hostname": "192.168.57.131", "username": "monitor", "password": "123"},
    {"hostname": "192.168.57.130", "username": "monitor", "password": "123"},
    {"hostname": "192.168.57.129", "username": "monitor", "password": "123"}
]

# Configuration de la base de données
db_config = {
    "host": "192.168.57.131",
    "user": "bdduser",
    "password": "123",
    "database": "bdd"
}

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

# Fonction pour envoyer un email
def send_alert_email(server, cpu_usage, ram_usage, disk_usage):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ADMIN_EMAIL
    msg['Subject'] = f"ALERTE : Ressources critiques sur {server['hostname']}"

    body = f"""
    Le serveur {server['hostname']} a dépassé les seuils d'utilisation :
    - CPU : {cpu_usage}% (seuil: {CPU_THRESHOLD}%)
    - RAM : {ram_usage}% (seuil: {RAM_THRESHOLD}%)
    - Disque : {disk_usage}% (seuil: {DISK_THRESHOLD}%)
    """

    msg.attach(MIMEText(body, 'plain'))

    try:
        smtp_server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp_server.starttls()
        smtp_server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        smtp_server.sendmail(SENDER_EMAIL, ADMIN_EMAIL, text)
        smtp_server.quit()
        print(f"Email d'alerte envoyé à {ADMIN_EMAIL} pour {server['hostname']}")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email d'alerte : {e}")

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
        cpu_usage = float(cpu_output.split()[1].replace(',', '.'))

        # Récupération de l'utilisation de la RAM
        stdin, stdout, stderr = ssh.exec_command("free -m | grep 'Mem'")
        ram_output = stdout.read().decode()
        mem_info = ram_output.split()
        ram_usage = float(mem_info[2].replace(',', '.')) / float(mem_info[1].replace(',', '.')) * 100

        # Récupération de l'utilisation du disque
        stdin, stdout, stderr = ssh.exec_command("df -h | grep '/dev/sda1'")
        disk_output = stdout.read().decode()
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

        # Vérifier les seuils et envoyer une alerte si nécessaire
        if cpu_usage > CPU_THRESHOLD or ram_usage > RAM_THRESHOLD or disk_usage > DISK_THRESHOLD:
            send_alert_email(server, cpu_usage, ram_usage, disk_usage)

# Fonction pour supprimer les données de plus de 72 heures
def delete_old_data():
    cutoff = datetime.now() - timedelta(hours=72)
    cursor.execute("DELETE FROM sys_res WHERE timestamp < %s", (cutoff,))
    db.commit()
    print("Données de plus de 72 heures supprimées")

# Récupération et insertion des données pour chaque serveur
for server in servers:
    cpu_usage, ram_usage, disk_usage = get_system_resources(server)
    insert_data(server, cpu_usage, ram_usage, disk_usage)

# Suppression des anciennes données
delete_old_data()

# Fermeture de la connexion à la base de données
cursor.close()
db.close()
print("Connexion à la base de données fermée")
