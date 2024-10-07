import paramiko
import time

def ssh_login_sudo(host, username, password, sudo_password, mysql_user,mysql_password, mysql_command):
    # Initialiser le client SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connexion au serveur distant
        private_key_path = "/root/.ssh/id_rsa"
        passphrase = "123"
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path,password = passphrase)
        client.connect(host, username=username, pkey=private_key)
        print(f"Connexion réussie à {host} en tant que {username}")

        # Commande pour tester l'accès MySQL avec sudo
        ssh_command = f"echo {sudo_password} | sudo -S mysql -u{mysql_user} -p{mysql_password} -e \"{mysql_command}\""
#ssh_command = f"mysql -u{mysql_user} -p{mysql_password} -e \"{mysql_command}\""
        # Ouvrir le canal pour l'exécution de la commande
        stdin, stdout, stderr = client.exec_command(ssh_command)

        # Attendre quelques instants pour permettre à la commande de s'exécuter
        time.sleep(1)

        # Lire la sortie et les erreurs
        output = stdout.read().decode()
        error = stderr.read().decode()

        # Afficher les résultats
        if output:
            print("Sortie de la commande MySQL :")
            print(output)
        if error:
            print("Erreurs (si présentes) :")
            print(error)

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

    finally:
        # Fermer la connexion SSH
        client.close()

if __name__ == "__main__":
    # Informations de connexion
    host = "192.168.57.131"  # Adresse du serveur distant
    username = "monitor"  # Nom d'utilisateur SSH
    password = "123"  # Mot de passe SSH
    sudo_password = "123"  # Mot de passe sudo pour l'utilisateur
    
    # Informations MySQL/MariaDB
    mysql_user = "root"  # Utilisateur MySQL
    mysql_password = "root_password"  # Mot de passe MySQL
    mysql_command = "SHOW DATABASES;"  # Commande MySQL à exécuter

    # Appeler la fonction pour vérifier l'accès MySQL
    ssh_login_sudo(host, username, password, sudo_password, mysql_user, mysql_password, mysql_command)

