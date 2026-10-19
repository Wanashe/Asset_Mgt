from django.db import models
from django.contrib.auth.models import User


# ZESA Building / Location Dropdown Choices
LOCATION_CHOICES = [
    ('Borrowdale', 'Borrowdale'),
    ('Coleford', 'Coleford'),
    ('Glennorah', 'Glennorah'),
    ('GlenView', 'GlenView'),
    ('Kuwadzana', 'Kuwadzana'),
    ('Mabelreign', 'Mabelreign'),
    ('Makoni', 'Makoni'),
    ('Mbare', 'Mbare'),
    ('Mufakose', 'Mufakose'),
    ('Ruwa', 'Ruwa'),
    ('Showgrounds', 'Showgrounds'),
    ('WarrenPark', 'WarrenPark'),
    ('Waterfalls', 'Waterfalls'),
    ('wynne_st', 'Wynne St (wynne_st)'),
    ('Zengeza', 'Zengeza'),
]


class Location(models.Model):
    building = models.CharField(
        max_length=100,
        choices=LOCATION_CHOICES,
        default='Borrowdale',
        verbose_name="Location / Building"
    )
    floor = models.CharField(max_length=50)  # e.g., "1st Floor"
    room_number = models.CharField(max_length=50)  # e.g., "Room 102"

    def __str__(self):
        return f"{self.room_number}, {self.floor} ({self.get_building_display()})"


class Asset(models.Model):
    REGION_CHOICES = [
        ('Harare', 'Harare Region (based in Harare)'),
        ('Northern', 'Northern Region (based in Chinhoyi)'),
        ('Southern', 'Southern Region (based in Gweru)'),
        ('Eastern', 'Eastern Region (based in Mutare)'),
        ('Western', 'Western Region (based in Bulawayo)'),
    ]

    DEPARTMENT_CHOICES = [
        ('IT', 'IT'),
        ('Finance', 'Finance'),
        ('Procurement', 'Procurement'),
        ('HR', 'Human Resources (HR)'),
        ('Operations', 'Operations & Maintenance'),
        ('Administration', 'Administration'),
        ('Executive', 'Executive / Directorate'),
    ]

    CATEGORY_CHOICES = [
        ('Furniture', 'Furniture (Desks, Chairs, Cabinets)'),
        ('Appliance', 'Appliances (Heaters, Fans, Microwave)'),
        ('Electronics', 'Electronics & IT Equipment'),
    ]

    CONDITION_CHOICES = [
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Needs Repair', 'Needs Repair'),
        ('Damaged', 'Damaged'),
    ]

    name = models.CharField(max_length=150)  # Item Name / Description
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Furniture')
    
    # Identifiers
    asset_tag = models.CharField(max_length=50, unique=True)  # Compulsory Asset Code / Tag
    serial_number = models.CharField(max_length=100, blank=True, null=True)  # Optional Serial No.
    
    # Region, Department & Custodian
    region = models.CharField(max_length=50, choices=REGION_CHOICES, default='Harare')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='Administration')
    assigned_to = models.CharField(max_length=100, blank=True, null=True)  # Custodian / User Name
    
    # Audited Physical Location
    current_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    office_number = models.CharField(
        max_length=50,
        choices=LOCATION_CHOICES,
        blank=True,
        null=True,
        verbose_name="Location / Building"
    )  # Audited Office / Location Tag
    
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='Good')
    purchase_date = models.DateField(blank=True, null=True)
    
    # Audit Metadata
    checked_by = models.CharField(max_length=100, blank=True, null=True)
    date_checked = models.DateField(blank=True, null=True)
    signature = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        loc_str = self.get_office_number_display() if self.office_number else (str(self.current_location) if self.current_location else "Unassigned")
        sn_str = f" [S/N: {self.serial_number}]" if self.serial_number else ""
        return f"{self.name} ({self.asset_tag}){sn_str} [{self.region} / {self.department} / {loc_str}]"


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='tickets')
    issue_description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    reported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket for {self.asset.name} - Status: {self.status}"


class AssetTransfer(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='transfers')
    
    # Transfer Origins
    from_region = models.CharField(max_length=50, choices=Asset.REGION_CHOICES, blank=True, null=True)
    from_department = models.CharField(max_length=50, choices=Asset.DEPARTMENT_CHOICES, blank=True, null=True)
    from_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_from')
    from_office = models.CharField(max_length=50, choices=LOCATION_CHOICES, blank=True, null=True)
    from_person = models.CharField(max_length=100, blank=True, null=True)
    
    # Transfer Destination
    to_region = models.CharField(max_length=50, choices=Asset.REGION_CHOICES, blank=True, null=True)
    to_department = models.CharField(max_length=50, choices=Asset.DEPARTMENT_CHOICES, blank=True, null=True)
    to_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_to')
    to_office = models.CharField(max_length=50, choices=LOCATION_CHOICES, blank=True, null=True)
    to_person = models.CharField(max_length=100, blank=True, null=True)
    
    reason = models.TextField(blank=True, null=True)
    transferred_at = models.DateTimeField(auto_now_add=True)
    transferred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.to_region:
            self.asset.region = self.to_region
        if self.to_department:
            self.asset.department = self.to_department
        if self.to_location:
            self.asset.current_location = self.to_location
        if self.to_office:
            self.asset.office_number = self.to_office
        if self.to_person:
            self.asset.assigned_to = self.to_person
            
        self.asset.save()
        super().save(*args, **kwargs)

    def __str__(self):
        date_str = self.transferred_at.strftime('%Y-%m-%d') if self.transferred_at else "Pending"
        return f"Transfer of {self.asset.name} ({self.asset.asset_tag}) on {date_str}"