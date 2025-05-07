from datetime import timezone
import uuid
import qrcode
from io import BytesIO  
from django.core.files.base import ContentFile
import os
from django.conf import settings
from .models import QR_Code

import qrcode
from io import BytesIO  
from django.core.files.base import ContentFile
from .models import QR_Code

def generate_qr_code(request):
    """
    Generate a unique QR code for today's attendance.
    """
    employee = request.user  # Assuming request.user is linked to Attendance_Employee_data
    today = timezone.now().date()
    qr_data = f"attendance/{employee.id}/{today}"  # 🔹 Dynamic QR Code URL

    # Check if QR code already exists
    qr_code, created = QR_Code.objects.get_or_create(
        code=qr_data,
        defaults={"location": "Office"}
    )

    if not created:
        return qr_code  

    # Generate the QR Code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    # Save image to model
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    if hasattr(qr_code, "image"):
        qr_code.image.save(f"qr_{employee.id}_{today}.png", ContentFile(buffer.getvalue()), save=True)

    return qr_code

