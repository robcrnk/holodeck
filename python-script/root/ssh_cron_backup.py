import os
import paramiko
from datetime import datetime

# Configurations
BACKUP_DIR = '~/backup'  # Répertoire local où stocker les sauvegardes
DATABASE_NAME = 'bdd'
DATABASE_USER = 'monitor'
DATABASE_PASSWORD = '123'
REMOTE_HOST = '192.168.57.131'  # Adresse IP ou nom d'hôte de la VM distante (MariaDB)
REMOTE_USER = 'monitor'  # Utilisateur SSH de la VM distante
PRIVATE_KEY_PATH = '/root/.ssh/id_rsa'  # Clé privée pour se connecter au serveur distant
NUMBER_OF_BACKUPS_TO_KEEP = 7  # Garder uniquement les 7 dernières sauvegardes
passphrase = '123'

# Fonction pour se connecter à la VM distante via SSH et exécuter la commande de dump de MariaDB
def backup_database():
    # Horodatage pour le nom de fichier
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Chemin du fichier de sauvegarde local
    backup_file = f'{BACKUP_DIR}/db_backup_{timestamp}.sql'

    # Commande à exécuter sur le serveur distant pour effectuer le dump
    dump_command = f'mysqldump -u {DATABASE_USER} -p{DATABASE_PASSWORD} {DATABASE_NAME} > {backup_file}'

    try:
        # Charger la clé privée
        key = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY_PATH, password=passphrase)

        # Initialiser la connexion SSH
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(REMOTE_HOST, username=REMOTE_USER, pkey=key)

        # Exécuter la commande de dump de la base de données sur la VM distante
        stdin, stdout, stderr = client.exec_command(dump_command, timeout=40)

        # Récupérer les erreurs s'il y en a
        errors = stderr.read().decode('utf-8')
        if errors:
            print(f"Erreur lors de l'exécution de la commande sur le serveur distant : {errors}")
        else:
            print(f"Sauvegarde réussie : {backup_file}")

        # Fermer la connexion SSH
        client.close()

        return backup_file  # Retourne le chemin du fichier de sauvegarde
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la base de données : {e}")
        return None

# Fonction pour supprimer les anciennes sauvegardes sur la machine distante
# Fonction pour supprimer les anciennes sauvegardes sur la machine distante
def clean_old_backups_remote():
    try:
        # Charger la clé privée
        key = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY_PATH, password=passphrase)

        # Initialiser la connexion SSH
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(REMOTE_HOST, username=REMOTE_USER, pkey=key)

        # Commande pour lister les sauvegardes dans le répertoire de backup distant et les trier par date
        list_backups_cmd = f'ls -1t {BACKUP_DIR}/db_backup_*.sql'
        stdin, stdout, stderr = client.exec_command(list_backups_cmd)

        # Lire la sortie
        backup_files = stdout.read().decode().splitlines()

        # Afficher les sauvegardes trouvées
        print(f"Nombre total de sauvegardes trouvées : {len(backup_files)}")

        # Vérifier si plus de 7 fichiers existent
        if len(backup_files) > NUMBER_OF_BACKUPS_TO_KEEP:
            backups_to_delete = backup_files[NUMBER_OF_BACKUPS_TO_KEEP:]  # Récupère les fichiers à supprimer

            for backup in backups_to_delete:
                delete_cmd = f'rm {backup}'  # Utiliser le chemin correct du fichier
                stdin, stdout, stderr = client.exec_command(delete_cmd)  # Supprime chaque fichier
                
                # Vérifier les erreurs lors de la suppression
                errors = stderr.read().decode('utf-8')
                if errors:
                    print(f"Erreur lors de la suppression de {backup} : {errors}")
                else:
                    print(f"Suppression de la sauvegarde : {backup}")
        else:
            print("Aucune sauvegarde à supprimer.")

        # Fermer la connexion SSH
        client.close()

    except Exception as e:
        print(f"Erreur lors de la suppression des anciennes sauvegardes : {e}")

if __name__ == '__main__':
    backup_database()
    clean_old_backups_remote()
