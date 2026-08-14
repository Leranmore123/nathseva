from django.db import models
import uuid
from django.contrib.auth.hashers import make_password


def upload_signature(instance, filename):
    return f'pan_docs/{instance.order_id}/signature_{filename}'

def upload_photo(instance, filename):
    return f'pan_docs/{instance.order_id}/photo_{filename}'

def upload_epan(instance, filename):
    return f'pan_docs/{instance.order_id}/epan_{filename}'


class Retailer(models.Model):
    retailer_id    = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_id        = models.CharField(max_length=50, unique=True)
    password       = models.CharField(max_length=255)
    full_name      = models.CharField(max_length=100)
    mobile         = models.CharField(max_length=15, unique=True)
    email          = models.EmailField(max_length=100, blank=True)
    state          = models.CharField(max_length=50, blank=True)
    address        = models.TextField(blank=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_verified    = models.BooleanField(default=False)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw):
        self.password = make_password(raw)

    def __str__(self):
        return f"{self.user_id} — {self.full_name}"


class PaymentRequest(models.Model):
    STATUS = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]

    retailer   = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='payments')
    utr_number = models.CharField(max_length=100)
    screenshot = models.ImageField(upload_to='payment_screenshots/', blank=True, null=True)
    amount     = models.DecimalField(max_digits=8, decimal_places=2, default=99)
    status     = models.CharField(max_length=20, choices=STATUS, default='pending')
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at= models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.retailer.user_id} — ₹{self.amount} — {self.status}"


class WalletTransaction(models.Model):
    TX_TYPE = [('credit', 'Credit'), ('debit', 'Debit')]
    STATUS  = [('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')]

    retailer            = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='wallet_txns')
    amount              = models.DecimalField(max_digits=10, decimal_places=2)
    tx_type             = models.CharField(max_length=10, choices=TX_TYPE)
    status              = models.CharField(max_length=20, choices=STATUS, default='pending')
    payment_provider    = models.CharField(max_length=50, blank=True)
    provider_order_id   = models.CharField(max_length=200, blank=True)
    provider_payment_id = models.CharField(max_length=200, blank=True)
    note                = models.TextField(blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.retailer.user_id} — {self.tx_type} ₹{self.amount} — {self.status}"


class PANApplication(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
    STATUS_CHOICES = [('PENDING', 'Pending'), ('COMPLETED', 'Completed')]

    # ✅ NEW: retailer se link — data isolation ke liye
    retailer    = models.ForeignKey(
        Retailer,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pan_applications'
    )

    order_id    = models.CharField(max_length=50, unique=True, editable=False)
    pan_number  = models.CharField(max_length=10)
    full_name   = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    dob         = models.DateField()
    gender      = models.CharField(max_length=10, choices=GENDER_CHOICES)
    epan_pdf    = models.FileField(upload_to=upload_epan, null=True, blank=True)
    signature   = models.ImageField(upload_to=upload_signature)
    photo       = models.ImageField(upload_to=upload_photo)
    amount      = models.DecimalField(max_digits=10, decimal_places=2, default=15.00)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    created_at  = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = 'PAN' + uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.full_name}"
class RCAdvanceApplication(models.Model):
    retailer        = models.ForeignKey(Retailer, on_delete=models.CASCADE)
    order_id        = models.CharField(max_length=40, unique=True)
    vehicle_number  = models.CharField(max_length=20)
    owner_name      = models.CharField(max_length=255, blank=True)
    vehicle_class   = models.CharField(max_length=100, blank=True)
    maker_model     = models.CharField(max_length=200, blank=True)
    fuel_type       = models.CharField(max_length=50, blank=True)
    rc_data         = models.JSONField(blank=True, null=True)
    amount          = models.DecimalField(max_digits=8, decimal_places=2)
    status          = models.CharField(max_length=10, default='pending')
    service_type    = models.CharField(max_length=20, default='advance')   # 👈 yeh line add karo
    created_at      = models.DateTimeField(auto_now_add=True)

    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_id} - {self.vehicle_number}"

class DLAllIndiaApplication(models.Model):
    retailer    = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='dl_allindia_applications')
    order_id    = models.CharField(max_length=40, unique=True)
    dl_number   = models.CharField(max_length=20)
    dob         = models.CharField(max_length=15, blank=True)   # DD/MM/YYYY jaisa form se aaya
    full_name   = models.CharField(max_length=255, blank=True)
    dl_data     = models.JSONField(blank=True, null=True)
    amount      = models.DecimalField(max_digits=8, decimal_places=2, default=25.00)
    status      = models.CharField(max_length=15, default='pending')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_id} - {self.dl_number}"

class DLKarnatakaApplication(models.Model):
    STATUS_CHOICES = [('success', 'Success'), ('failed', 'Failed'), ('pending', 'Pending')]

    retailer     = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name='dl_karnataka_applications')
    order_id     = models.CharField(max_length=40, unique=True)
    dl_number    = models.CharField(max_length=20, blank=True)
    dob          = models.CharField(max_length=15, blank=True)
    full_name    = models.CharField(max_length=255, blank=True)
    vehicle_type = models.CharField(max_length=100, blank=True)
    dl_data      = models.JSONField(blank=True, null=True)
    photo        = models.ImageField(upload_to='dl_karnataka/photos/', blank=True, null=True)
    signature    = models.ImageField(upload_to='dl_karnataka/signatures/', blank=True, null=True)
    amount       = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_id} - {self.dl_number}"


def upload_tailoring_photo(instance, filename):
    return f'tailoring_docs/{instance.order_id}/photo_{filename}'

def upload_tailoring_id(instance, filename):
    return f'tailoring_docs/{instance.order_id}/id_{filename}'

def upload_tailoring_cert(instance, filename):
    return f'tailoring_docs/{instance.order_id}/cert_{filename}'

def upload_tailoring_output_pdf(instance, filename):
    return f'tailoring_certs/{instance.order_id}/{filename}'


class TailoringCertificateApplication(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')]

    retailer             = models.ForeignKey(Retailer, on_delete=models.SET_NULL, null=True, blank=True, related_name='tailoring_applications')
    order_id             = models.CharField(max_length=50, unique=True, editable=False)
    full_name            = models.CharField(max_length=100)
    mobile_number        = models.CharField(max_length=10)
    email_id             = models.EmailField()
    gender               = models.CharField(max_length=10)
    date_of_birth        = models.DateField()
    father_husband_name  = models.CharField(max_length=100)
    state                = models.CharField(max_length=50)
    district             = models.CharField(max_length=50)
    taluk                = models.CharField(max_length=50)
    village              = models.CharField(max_length=50)
    pin_code             = models.CharField(max_length=6)
    physical_handicap    = models.CharField(max_length=10)
    address              = models.TextField()
    highest_education    = models.CharField(max_length=50)
    photo                = models.ImageField(upload_to=upload_tailoring_photo, null=True, blank=True)
    id_proof             = models.FileField(upload_to=upload_tailoring_id, null=True, blank=True)
    education_cert       = models.FileField(upload_to=upload_tailoring_cert, null=True, blank=True)
    output_pdf           = models.FileField(upload_to=upload_tailoring_output_pdf, null=True, blank=True)
    rejection_reason     = models.TextField(blank=True)
    amount               = models.DecimalField(max_digits=10, decimal_places=2, default=450.00)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at           = models.DateTimeField(auto_now_add=True)
    processed_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = 'TLR' + uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.full_name}"


def upload_computer_photo(instance, filename):
    return f'computer_docs/{instance.order_id}/photo_{filename}'

def upload_computer_output_pdf(instance, filename):
    return f'computer_certs/{instance.order_id}/{filename}'


class BasicComputerCertificateApplication(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')]

    retailer          = models.ForeignKey(Retailer, on_delete=models.SET_NULL, null=True, blank=True, related_name='computer_applications')
    order_id          = models.CharField(max_length=50, unique=True, editable=False)
    student_name      = models.CharField(max_length=100)
    father_name       = models.CharField(max_length=100)
    mother_name       = models.CharField(max_length=100)
    date_of_birth     = models.DateField()
    gender            = models.CharField(max_length=10)
    qualification     = models.CharField(max_length=50)
    cast_category     = models.CharField(max_length=20)
    state             = models.CharField(max_length=50)
    district          = models.CharField(max_length=50)
    full_address      = models.TextField()
    pin_code          = models.CharField(max_length=6)
    mobile_no         = models.CharField(max_length=10)
    email_id          = models.EmailField()
    photo             = models.ImageField(upload_to=upload_computer_photo, null=True, blank=True)
    output_pdf        = models.FileField(upload_to=upload_computer_output_pdf, null=True, blank=True)
    rejection_reason  = models.TextField(blank=True)
    amount            = models.DecimalField(max_digits=10, decimal_places=2, default=400.00)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at        = models.DateTimeField(auto_now_add=True)
    processed_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = 'CMP' + uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.student_name}"


def upload_udyam_aadhaar(instance, filename):
    return f'udyam_docs/{instance.order_id}/aadhaar_{filename}'

def upload_udyam_pan(instance, filename):
    return f'udyam_docs/{instance.order_id}/pan_{filename}'

def upload_udyam_passbook(instance, filename):
    return f'udyam_docs/{instance.order_id}/passbook_{filename}'

def upload_udyam_output_pdf(instance, filename):
    return f'udyam_certs/{instance.order_id}/{filename}'


class UdyamRegistrationApplication(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')]

    retailer             = models.ForeignKey(Retailer, on_delete=models.SET_NULL, null=True, blank=True, related_name='udyam_applications')
    order_id             = models.CharField(max_length=50, unique=True, editable=False)
    
    # Personal Info
    applicant_name       = models.CharField(max_length=100)
    aadhaar_no           = models.CharField(max_length=12, blank=True)
    date_of_birth        = models.DateField(null=True, blank=True)
    email_id             = models.EmailField(blank=True)
    mobile_no            = models.CharField(max_length=10, blank=True)
    pan_card_no          = models.CharField(max_length=10, blank=True)

    # Business Info
    business_name        = models.CharField(max_length=100, blank=True)
    business_type        = models.CharField(max_length=50, blank=True)
    business_address     = models.TextField(blank=True)
    working_member       = models.CharField(max_length=10, blank=True)
    gst_number           = models.CharField(max_length=15, blank=True)
    annual_income        = models.CharField(max_length=20, blank=True)

    # Bank Info
    bank_name            = models.CharField(max_length=100, blank=True)
    ifsc_code            = models.CharField(max_length=11, blank=True)
    account_no           = models.CharField(max_length=20, blank=True)

    # Documents
    aadhaar_file         = models.FileField(upload_to=upload_udyam_aadhaar, null=True, blank=True)
    pan_file             = models.FileField(upload_to=upload_udyam_pan, null=True, blank=True)
    bank_passbook_file   = models.FileField(upload_to=upload_udyam_passbook, null=True, blank=True)

    output_pdf           = models.FileField(upload_to=upload_udyam_output_pdf, null=True, blank=True)
    rejection_reason     = models.TextField(blank=True)
    amount               = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at           = models.DateTimeField(auto_now_add=True)
    processed_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = 'UDY' + uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.applicant_name}"


def upload_pvc_pdf(instance, filename):
    return f'pvc_docs/{instance.order_id}/{filename}'

def upload_pvc_output_pdf(instance, filename):
    return f'pvc_certs/{instance.order_id}/{filename}'


class PVCMakerApplication(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')]

    retailer             = models.ForeignKey(Retailer, on_delete=models.SET_NULL, null=True, blank=True, related_name='pvc_applications')
    order_id             = models.CharField(max_length=50, unique=True, editable=False)
    
    pvc_card_type        = models.CharField(max_length=50)
    service_types        = models.CharField(max_length=100, blank=True)
    agent_mobile         = models.CharField(max_length=10)
    customer_mobile      = models.CharField(max_length=10)
    full_name            = models.CharField(max_length=100)
    village              = models.CharField(max_length=100)
    taluk                = models.CharField(max_length=100)
    district             = models.CharField(max_length=100)
    pincode              = models.CharField(max_length=6)
    delivery_address     = models.TextField()

    pdf_file             = models.FileField(upload_to=upload_pvc_pdf, null=True, blank=True)
    card_number          = models.CharField(max_length=100, blank=True)

    output_pdf           = models.FileField(upload_to=upload_pvc_output_pdf, null=True, blank=True)
    rejection_reason     = models.TextField(blank=True)
    amount               = models.DecimalField(max_digits=10, decimal_places=2, default=150.00)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at           = models.DateTimeField(auto_now_add=True)
    processed_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = 'PVC' + uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.full_name}"


def upload_cibil_output_pdf(instance, filename):
    return f'cibil_reports/{instance.order_id}/{filename}'


class CibilScoreApplication(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')]

    retailer             = models.ForeignKey(Retailer, on_delete=models.SET_NULL, null=True, blank=True, related_name='cibil_applications')
    order_id             = models.CharField(max_length=50, unique=True, editable=False)
    
    first_name           = models.CharField(max_length=50)
    last_name            = models.CharField(max_length=50)
    pan_number           = models.CharField(max_length=10)
    mobile_number        = models.CharField(max_length=10)
    aadhaar_number       = models.CharField(max_length=12)

    output_pdf           = models.FileField(upload_to=upload_cibil_output_pdf, null=True, blank=True)
    rejection_reason     = models.TextField(blank=True)
    amount               = models.DecimalField(max_digits=10, decimal_places=2, default=120.00)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at           = models.DateTimeField(auto_now_add=True)
    processed_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = 'CIB' + uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.first_name} {self.last_name}"


def upload_aadhaar_pdf_output(instance, filename):
    return f'aadhaar_pdf_reports/{instance.order_id}/{filename}'


class AadhaarPdfApplication(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')]

    retailer             = models.ForeignKey(Retailer, on_delete=models.SET_NULL, null=True, blank=True, related_name='aadhaar_pdf_applications')
    order_id             = models.CharField(max_length=50, unique=True, editable=False)
    
    uid_number           = models.CharField(max_length=12)
    name                 = models.CharField(max_length=100)

    output_pdf           = models.FileField(upload_to=upload_aadhaar_pdf_output, null=True, blank=True)
    rejection_reason     = models.TextField(blank=True)
    amount               = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at           = models.DateTimeField(auto_now_add=True)
    processed_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = 'ADR' + uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.name} ({self.uid_number})"


def upload_eid_slip(instance, filename):
    return f'eid_slips/{instance.order_id}/{filename}'

def upload_eid_output_pdf(instance, filename):
    return f'eid_reports/{instance.order_id}/{filename}'


class EidToUidApplication(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')]

    retailer             = models.ForeignKey(Retailer, on_delete=models.SET_NULL, null=True, blank=True, related_name='eid_to_uid_applications')
    order_id             = models.CharField(max_length=50, unique=True, editable=False)
    
    eid_number           = models.CharField(max_length=28)
    upload_slip          = models.FileField(upload_to=upload_eid_slip)

    output_pdf           = models.FileField(upload_to=upload_eid_output_pdf, null=True, blank=True)
    rejection_reason     = models.TextField(blank=True)
    amount               = models.DecimalField(max_digits=10, decimal_places=2, default=750.00)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at           = models.DateTimeField(auto_now_add=True)
    processed_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = 'EID' + uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.eid_number}"


def upload_lms_output_pdf(instance, filename):
    return f'lms_certificates/{instance.order_id}/{filename}'


class LMSCertificateApplication(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')]

    retailer             = models.ForeignKey(Retailer, on_delete=models.SET_NULL, null=True, blank=True, related_name='lms_certificate_applications')
    order_id             = models.CharField(max_length=50, unique=True, editable=False)
    
    full_name            = models.CharField(max_length=100)
    aadhaar_number       = models.CharField(max_length=12)
    email                = models.EmailField()
    mobile               = models.CharField(max_length=10)
    state                = models.CharField(max_length=100)
    district             = models.CharField(max_length=100)
    taluka               = models.CharField(max_length=100)
    native_place         = models.CharField(max_length=100)

    output_pdf           = models.FileField(upload_to=upload_lms_output_pdf, null=True, blank=True)
    rejection_reason     = models.TextField(blank=True)
    amount               = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at           = models.DateTimeField(auto_now_add=True)
    processed_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = 'LMS' + uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.full_name} ({self.aadhaar_number})"


class PanToAadhaarApplication(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')]

    retailer             = models.ForeignKey(Retailer, on_delete=models.SET_NULL, null=True, blank=True, related_name='pan_to_aadhaar_applications')
    order_id             = models.CharField(max_length=50, unique=True, editable=False)
    
    pan_number           = models.CharField(max_length=10)
    aadhaar_number       = models.CharField(max_length=12, blank=True)

    rejection_reason     = models.TextField(blank=True)
    amount               = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at           = models.DateTimeField(auto_now_add=True)
    processed_at         = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = 'P2A' + uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.pan_number}"



