import paramiko

# Commande à exécuter sur l'hôte distant
command = "ls /home/"

# Informations sur l'hôte distant
host = "192.168.57.129"
username = "monitor"

# Chemin vers la clé privée SSH (remplacer par le chemin de ta clé privée)
private_key_path = "/root/.ssh/id_rsa"  # Chemin vers ta clé privée sur Windows
passphrase = "123"
# Création d'un client SSH
client = paramiko.client.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Chargement de la clé privée SSH
private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password = passphrase)

# Connexion à l'hôte distant avec la clé privée
client.connect(host, username=username, pkey=private_key)

# Exécution de la commande
_stdin, _stdout, _stderr = client.exec_command(command)
print(_stdout.read().decode())

# Fermeture de la connexion
client.close()
