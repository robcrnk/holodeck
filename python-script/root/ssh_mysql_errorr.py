import mariadb
import paramiko
import re
from datetime import datetime

def parse_log_file(log_file, ssh_client, sudo_password):
    tentatives_acces = []
    try:
        stdin, stdout, stderr = ssh_client.exec_command(f'sudo cat {log_file}', get_pty=True)
        stdin.write(f'{sudo_password}\n')
        stdin.flush()
        log_content = stdout.read().decode()
        for line in log_content.splitlines():
            match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Access denied for user '([^']+)'@'([^']+)'", line)
            if match:
                timestamp = match.group(1)
                username = match.group(2)
                ip_address = match.group(3)
                tentatives_acces.append((username, ip_address, timestamp))
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier de log : {e}")
    return tentatives_acces

def store_access_attempts(tentatives_acces):
    try:
        conn = mariadb.connect(
            user="jtombi",
            password="salakae",
            host="192.168.75.129",
            port=3306,  # Port spécifié ici
            database="bb_sql"
        )
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_attempts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255),
                ip_address VARCHAR(255),
                timestamp DATETIME
            )
        """)

        for attempt in tentatives_acces:
            print(f"Insertion : {attempt}")  # Impression pour débogage
            cursor.execute("""
                INSERT INTO access_attempts (username, ip_address, timestamp)
                VALUES (%s, %s, %s)
            """, attempt)

        conn.commit()
        print("Tentatives d'accès enregistrées avec succès !")

    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement des tentatives d'accès : {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    chemin_fichier_log = "/var/log/mysql/mysql-error.log"
    hote_ssh = "192.168.75.129"
    utilisateur_ssh = "jtombi"
    mot_de_passe_ssh = "salakae"
    mot_de_passe_sudo = "salakae"

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hote_ssh, username=utilisateur_ssh, password=mot_de_passe_ssh)

    tentatives_acces = parse_log_file(chemin_fichier_log, ssh_client, mot_de_passe_sudo)
    store_access_attempts(tentatives_acces)

    ssh_client.close()
