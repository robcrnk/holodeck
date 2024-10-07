import paramiko
import mariadb
from datetime import datetime, timedelta

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
