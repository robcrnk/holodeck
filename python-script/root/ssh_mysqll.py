import paramiko
import mariadb
import sys

def ssh_login_mysql(host, username, password):
    # Connexion SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    conn = None  # Initialisation de la variable

    try:
        client.connect(host, username=username, password=password)
        print(f"Connexion SSH réussie à {host} en tant que {username}")

        # Connexion à la base de données MariaDB
        conn = mariadb.connect(user="bdduser", password="123", host="192.168.57.132", port=3306, database="bdd")
        print("Connexion à la base de données MariaDB réussie")

        # Exécutez vos opérations sur la base de données ici (par exemple, SELECT, INSERT, UPDATE, etc.)
 # Boucle pour exécuter des commandes SQL
        while True:
            command = input("Entrez votre commande SQL (ou 'exit' pour quitter) : ")
            if command.lower() == 'exit':
                break

            cursor = conn.cursor()
            try:
                cursor.execute(command)
                if command.strip().lower().startswith("select"):
                    results = cursor.fetchall()
                    for row in results:
                        print(row)
                else:
                    conn.commit()
                    print(f"Commande exécutée avec succès : {command}")
            except mariadb.Error as e:
                print(f"Erreur lors de l'exécution de la commande : {e}")
            finally:
                cursor.close()

    except paramiko.SSHException as ssh_e:
        print(f"Erreur SSH : {ssh_e}")
    except mariadb.Error as db_e:
        print(f"Erreur de base de données : {db_e}")
        sys.exit(1)
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        sys.exit(1)

    finally:
        # Fermez les connexions
        if conn:
            conn.close()
        client.close()

ssh_login_mysql(host='192.168.57.132', username='monitor', password='123')



