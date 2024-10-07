import yagmail

def send_email():
    # Remplacez ces valeurs par vos informations
    sender_email = "testmail621313@gmail.com"
    password = "40ad1ef0D"  # Utilisez un mot de passe d'application si possible
    recipient_email = "testmail621313@gmail.com"
    
    # Initialisation de yagmail
    yag = yagmail.SMTP("testmail621313", "40ad1ef0D")
    
    # Envoyer un email
    yag.send(
        to=recipient_email,
        subject="Test de yagmail",
        contents="Ceci est un email de test envoyé via yagmail."
    )
    print("Email envoyé avec succès !")

send_email()
