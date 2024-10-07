import mariadb
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def fetch_data_from_db(db_user, db_password, db_host, db_port, db_name):
    conn = None
    try:
        conn = mariadb.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=int(db_port),
            database=db_name
        )
        cursor = conn.cursor()

        tables = ["error_www", "error_mariadb", "error_sftp"]
        data = {}

        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            data[table] = rows

        return data

    except mariadb.Error as e:
        print(f"Erreur lors de la connexion à la base de données : {e}")
        return None
    finally:
        if conn:
            conn.close()

def send_email(data, sender_email, receiver_email, password):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Rapport des erreurs d'authentification Mariadb/SFTP/Web"

    body = ""
    for table, rows in data.items():
        body += f"Table: {table}\n"
        for row in rows:
            body += f"{row}\n"
        body += "\n"

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print("E-mail envoyé avec succès !")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail : {e}")

if __name__ == "__main__":
    DB_USER = "bdduser"
    DB_PASSWORD = "123"
    DB_HOST = "192.168.57.131"
    DB_PORT = "3306"
    DB_NAME = "bdd"
    SENDER_EMAIL = "testmail621313@gmail.com"
    RECEIVER_EMAIL = "robin.mahu@laplateforme.io"
    EMAIL_PASSWORD = "xqod bajt bryx edzj"  # Utilisez un mot de passe d'application

    data = fetch_data_from_db(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
    if data:
        send_email(data, SENDER_EMAIL, RECEIVER_EMAIL, EMAIL_PASSWORD)
