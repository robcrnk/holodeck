import paramiko
import time

def ssh_login_sudo(host, username, password, sudo_password, command):
    # Initialiser le client SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connexion au serveur distant
        private_key_path = "/root/.ssh/id_rsa"
        passphrase = "123"
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password = passphrase)
        client.connect(host, username=username, pkey=private_key)
        print(f"Connexion réussie à {host} en tant que {username}")

        # Exécution de la commande en tant que superutilisateur (sudo)
        ssh_command = f"sudo -S -p '' {command}"

        # Ouvrir le canal pour l'exécution de la commande
        stdin, stdout, stderr = client.exec_command(ssh_command)

        # Fournir le mot de passe sudo
        stdin.write(sudo_password + "\n")
        stdin.flush()

        # Attendre quelques instants pour permettre à la commande de s'exécuter
        time.sleep(1)

        # Lire la sortie et les erreurs
        output = stdout.read().decode()
        error = stderr.read().decode()

        # Afficher les résultats
        if output:
            print("Sortie de la commande :")
            print(output)

        if error:
            print("Erreurs (si présentes) :")
            print(error)

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

    finally:
        # Fermer la connexion SSH
        client.close()
        print("Connexion fermée")

if __name__ == "__main__":
    # Informations de connexion
    host = "192.168.57.130"
    username = "monitor"
    password = "123"
    sudo_password = "123"  # Mot de passe sudo pour l'utilisateur
    command = "ls /root"   # Commande à exécuter avec sudo

    # Appeler la fonction pour exécuter la commande avec sudo
    ssh_login_sudo(host, username, password, sudo_password, command)
