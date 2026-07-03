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
    shop_name      = models.CharField(max_length=150, blank=True)
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