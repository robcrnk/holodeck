import mariadb
import paramiko
import re
from datetime import datetime

def read_log_file_via_ssh_www(ssh_client, remote_file_path, sudo_password):
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

def parse_log_content_www(log_content):
    tentatives_acces = []
    try:
        for line in log_content.splitlines():
            print(f"Analyse de la ligne : {line}")  # Débogage
            # Nouvelle expression régulière adaptée aux logs Nginx
            match_http = re.search(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[error\] \d+#\d+: \*\d+ user \"([^\"]+)\" was not found in \"/[^\"]+\", client: ([\d\.]+)", line)
            if match_http:
                timestamp_str = match_http.group(1)
                timestamp = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
                username = match_http.group(2)
                ip_address = match_http.group(3)
                tentatives_acces.append((username, ip_address, timestamp))
                print(f"Erreur d'authentification HTTP trouvée : {username}, {ip_address}, {timestamp}")  # Débogage
            else:
                print("Pas de correspondance trouvée pour cette ligne.")  # Débogage
    except Exception as e:
        print(f"Erreur lors de l'analyse du contenu du fichier de log : {e}")
    return tentatives_acces

def store_access_attempts_www(tentatives_acces):
    try: 
        conn = mariadb.connect(
            user="bdduser",
            password="123",
            host="192.168.57.131",
            port=3306,
            database="bdd"
        )
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_www (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255),
                ip_address VARCHAR(255),
                timestamp DATETIME
            )
        """)

        for attempt in tentatives_acces:
            print(f"Insertion : {attempt}")  # Débogage
            cursor.execute("""
                INSERT INTO error_www (username, ip_address, timestamp)
                VALUES (%s, %s, %s)
            """, attempt)

        conn.commit()
        print("Tentatives d'accès enregistrées avec succès !")

    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement des tentatives d'accès : {e}")
    finally:
        if conn:
            conn.close()

# Paramètres de connexion SSH
remote_file_path = "/var/log/nginx/error.log"
sudo_password = "123"
passphrase = "123"
hote_ssh = "192.168.57.130"
utilisateur_ssh = "monitor"
chemin_cle_privee = r"/root/.ssh/id_rsa"

# Connexion SSH
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh_client.connect(hote_ssh, username=utilisateur_ssh, key_filename=chemin_cle_privee, password=passphrase)
    log_content = read_log_file_via_ssh_www(ssh_client, remote_file_path, sudo_password)
    
    if log_content:
        tentatives_acces = parse_log_content_www(log_content)
        if tentatives_acces:
            store_access_attempts_www(tentatives_acces)
        else:
            print("Aucune tentative d'accès trouvée dans les logs.")
finally:
    ssh_client.close()
