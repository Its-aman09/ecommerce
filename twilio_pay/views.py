from django.shortcuts import render
from django.conf import settings
from .models import OTP
from twilio.rest import Client
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML

# 1️⃣ Send OTP
def send_otp(request):
    if request.method == "POST":
        phone = request.POST.get("phone")

        otp_obj = OTP(phone=phone)
        otp_code = otp_obj.generate_otp()
        otp_obj.save()

        # Send SMS via Twilio
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f"Your OTP is {otp_code}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )

        return render(request, "twilio_pay/verify_otp.html", {"phone": phone})

    return render(request, "twilio_pay/send_otp.html")


# 2️⃣ Verify OTP
def verify_otp(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        code = request.POST.get("otp")

        otp_obj = OTP.objects.filter(phone=phone).last()

        if otp_obj and otp_obj.code == code:
            return render(request, "twilio_pay/order_confirmed.html", {"phone": phone})

        return render(request, "twilio_pay/verify_otp.html", {
            "phone": phone,
            "error": "Invalid OTP. Try again."
        })


# 3️⃣ Generate PDF receipt
def generate_receipt(request):
    context = {
        "name": "Aman Kumar",
        "phone": "9999999999",
        "order_id": "ORD123456",
        "amount": 500,
    }
    html = render_to_string("twilio_pay/receipt.html", context)
    pdf = HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="receipt.pdf"'
    return response
