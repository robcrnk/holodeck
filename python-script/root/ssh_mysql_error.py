import mariadb
import re
import paramiko
from datetime import datetime

def parse_log_file(log_file, ssh_client, sudo_password):
    tentatives_acces = []
    try:
        print("Lecture du fichier de log...", flush=True)
        stdin, stdout, stderr = ssh_client.exec_command(f'sudo cat {log_file}', get_pty=True)
        stdin.write(f'{sudo_password}\n')
        stdin.flush()
        log_content = stdout.read().decode()
        print(f"Contenu du fichier de log : {log_content[:500]}", flush=True)
        for line in log_content.splitlines():
            match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Access denied for user '([^']+)'@'([^']+)'", line)
            if match:
                timestamp = match.group(1)
                username = match.group(2)
                ip_address = match.group(3)
                tentatives_acces.append((username, ip_address, timestamp))
                print(f"Tentative d'accès détectée : {username}, {ip_address}, {timestamp}", flush=True)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier de log : {e}", flush=True)
    return tentatives_acces

def store_access_attempts(tentatives_acces):
    try:
        print("Connexion à la base de données...", flush=True)
        conn = mariadb.connect(
            user="bdduser",
            password="123",
            host="192.168.57.131",
            port=3306,
            database="bdd"
        )
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_mariadb (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255),
            ip_address VARCHAR(255),
            timestamp DATETIME
        )
        """)

        for attempt in tentatives_acces:
#            print(f"Insertion : {attempt}")
            cursor.execute("""
                INSERT INTO error_mariadb (username, ip_address, timestamp)
                VALUES (%s, %s, %s)
            """, attempt)

        conn.commit()
        print("Tentatives d'accès enregistrées avec succès !", flush=True)

    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement des tentatives d'accès : {e}", flush=True)
    finally:
        if conn:
            conn.close()

# Utilisation
chemin_fichier_log = "/var/log/mysql/mysql-error.log"
hote_ssh = "192.168.57.131"
utilisateur_ssh = "monitor"
ssh_priv = "/root/.ssh/id_rsa"
mot_de_passe_sudo = "123"
passphrase = "123"

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    print("Connexion au serveur SSH...", flush=True)
    mypkey = paramiko.RSAKey.from_private_key_file(ssh_priv, password=passphrase)
    ssh_client.connect(hote_ssh, username=utilisateur_ssh, pkey=mypkey)
    print("Connecté au serveur SSH.", flush=True)

    tentatives_acces = parse_log_file(chemin_fichier_log, ssh_client, mot_de_passe_sudo)
    store_access_attempts(tentatives_acces)

finally:
    ssh_client.close()
    print("Connexion SSH fermée.", flush=True)
