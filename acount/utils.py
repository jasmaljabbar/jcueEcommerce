import pyotp
from datetime import datetime, timedelta
from django.core.mail import EmailMessage


def send_otp(request):
    totp = pyotp.TOTP(pyotp.random_base32(), interval=60)
    otp = totp.now()
    request.session['otp_key'] = totp.secret
    otp_valid = datetime.now() + timedelta(minutes=1)
    request.session['otp_valid'] = str(otp_valid)
    print(otp)
    

    mail = request.session['mail']
    subject = 'Verify your account'
    msg = f"Your otp is {otp}"
    from_email = 'jcuejqtips@gmail.com'
    reciever = [mail]

    try:
        email = EmailMessage(subject, msg, from_email, reciever)
        email.send()
    except Exception as e:
        print(f"Failed to send otp {str(e)}")