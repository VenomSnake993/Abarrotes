from dotenv import load_dotenv
import os
import secrets
import string
from email.message import EmailMessage
import smtplib

######################################################################################################################################
# Funtion to generate a random code
def codeGenerate():
    letters = string.ascii_letters
    numbers = string.digits
    alphabet= letters + numbers
    sizeCode= 6
    password = ''

    for i in range(sizeCode):
        password += ''.join(secrets.choice(alphabet)).upper()

    return password
######################################################################################################################################

# Load Environment Variables
load_dotenv()

######################################################################################################################################
# Function to send an email
def sendSimpleEmail(sender, recipent, message, subject):
    try:
        email = EmailMessage()
        email['Subject'] = subject
        email['From'] = sender
        email['To'] = recipent
        email.set_content(message)

        flatServer = smtplib.SMTP_SSL(os.getenv('SMPT_SSL'))
        flatServer.login(sender, os.getenv('MY_PASSWORD_EMAIL'))
        flatServer.sendmail(sender, recipent, email.as_string())
        flatServer.quit()

    except Exception as error:
        print("Error obtenido al enviar correo: ", error)
        return False
######################################################################################################################################
