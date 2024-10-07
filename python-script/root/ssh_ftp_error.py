import mariadb
import paramiko
import re
from datetime import datetime

def read_log_file_via_ssh_ftp(ssh_client, remote_file_path, sudo_password):
    try:
        stdin, stdout, stderr = ssh_client.exec_command(f'sudo cat {remote_file_path}', get_pty=True)
        stdin.write(f'{sudo_password}\n')
        stdin.flush()
        log_content = stdout.read().decode()
        print("Fichier lu depuis le serveur via SSH")
        return log_content
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier depuis le serveur via SSH : {e}")
        return None

def parse_log_content_ftp(log_content):
    tentatives_acces = []
    try:
        for line in log_content.splitlines():
            # Mise à jour de l'expression régulière pour correspondre au format des logs donnés
            match = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})[^\s]+ .*sshd\[\d+\]: Failed password for invalid user ([^ ]+) from ([\d\.]+) port \d+", line)
            if match:
                timestamp_str = match.group(1)
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
                username = match.group(2)
                ip_address = match.group(3)
                tentatives_acces.append((username, ip_address, timestamp))
    except Exception as e:
        print(f"Erreur lors de l'analyse du contenu du fichier de log : {e}")
    return tentatives_acces

def store_access_attempts_ftp(tentatives_acces):
    conn = None
    try:
        conn = mariadb.connect(
            user="bdduser",
            password="123",
            host="192.168.57.131",
            port=3306,
            database="bdd",
        )
        cursor = conn.cursor()

        # Création de la table si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_sftp (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255),
                ip_address VARCHAR(255),
                timestamp DATETIME
            )
        """)

        # Vérification des tentatives avant insertion
        if not tentatives_acces:
            print("Aucune tentative d'accès trouvée à insérer.")
            return

        for attempt in tentatives_acces:
            cursor.execute("""
                INSERT INTO error_sftp (username, ip_address, timestamp)
                VALUES (%s, %s, %s)
            """, attempt)

        conn.commit()
        print("Tentatives d'accès enregistrées avec succès !")

    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement des tentatives d'accès dans la base de données : {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

# Paramètres de connexion SSH
remote_file_path = "/var/log/auth.log"
sudo_password = "123"
hote_ssh = "192.168.57.129"
utilisateur_ssh = "monitor"
chemin_cle_privee = r"/root/.ssh/id_rsa"
passephrase = "123"

# Connexion SSH
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh_client.connect(hote_ssh, username=utilisateur_ssh, key_filename=chemin_cle_privee, password=passephrase)
    log_content = read_log_file_via_ssh_ftp(ssh_client, remote_file_path, sudo_password)
    
    if log_content:
        tentatives_acces = parse_log_content_ftp(log_content)
        store_access_attempts_ftp(tentatives_acces)
finally:
    ssh_client.close()
