import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Count, Q

# ReportLab dependencies for PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .models import Asset, Location, AssetTransfer


def home(request):
    """Renders the dashboard home page with asset summary metrics and breakdowns."""
    total_assets = Asset.objects.count()
    recent_assets = Asset.objects.order_by('-id')[:5]
    
    # Statistical breakdowns
    assets_by_region = Asset.objects.values('region').annotate(count=Count('id')).order_by('-count')
    assets_by_department = Asset.objects.values('department').annotate(count=Count('id')).order_by('-count')
    assets_by_condition = Asset.objects.values('condition').annotate(count=Count('id')).order_by('-count')

    return render(
        request,
        'assets/home.html',
        {
            'total_assets': total_assets,
            'recent_assets': recent_assets,
            'assets_by_region': assets_by_region,
            'assets_by_department': assets_by_department,
            'assets_by_condition': assets_by_condition,
        }
    )


def asset_sync_workspace(request):
    """Renders the Asset Tables inventory workspace with multi-field search (custodian, office, dept) and allocation count."""
    assets = Asset.objects.select_related('current_location').all()

    # Extract filter parameters from GET query string
    search_query = request.GET.get('q', '').strip()
    selected_region = request.GET.get('region', '').strip()
    selected_department = request.GET.get('department', '').strip()
    selected_condition = request.GET.get('condition', '').strip()
    selected_date = request.GET.get('date_checked', '').strip()

    # Apply search filter across Custodian Name, Office Number, Department, Item Name, Tags, and Serial Number
    if search_query:
        assets = assets.filter(
            Q(assigned_to__icontains=search_query) |      # Custodian Name search
            Q(office_number__icontains=search_query) |     # Office Number search
            Q(department__icontains=search_query) |        # Department search
            Q(name__icontains=search_query) |              # Item Description search
            Q(asset_tag__icontains=search_query) |         # Asset Tag search
            Q(serial_number__icontains=search_query)       # Serial Number search
        )

    # Apply dropdown filters
    if selected_region:
        assets = assets.filter(region=selected_region)
    if selected_department:
        assets = assets.filter(department=selected_department)
    if selected_condition:
        assets = assets.filter(condition=selected_condition)
    if selected_date:
        assets = assets.filter(date_checked=selected_date)

    assets = assets.order_by('-id')
    
    # Total count of matching assets allocated to the search criteria
    total_matching_assets = assets.count()

    return render(
        request,
        'assets/asset_sync.html',
        {
            'assets': assets,
            'total_assets': Asset.objects.count(),
            'total_matching_assets': total_matching_assets,
            'search_query': search_query,
            'selected_region': selected_region,
            'selected_department': selected_department,
            'selected_condition': selected_condition,
            'selected_date': selected_date,
            'region_choices': Asset.REGION_CHOICES if hasattr(Asset, 'REGION_CHOICES') else [],
            'department_choices': Asset.DEPARTMENT_CHOICES if hasattr(Asset, 'DEPARTMENT_CHOICES') else [],
            'condition_choices': Asset.CONDITION_CHOICES if hasattr(Asset, 'CONDITION_CHOICES') else [],
        }
    )


def asset_add(request):
    """Add a new asset record with separate asset tag, serial number, region, and location allocation."""
    if request.method == "POST":
        name = request.POST.get("name") or request.POST.get("description")
        asset_tag = request.POST.get("asset_tag") or request.POST.get("asset_number")
        serial_number = request.POST.get("serial_number", "").strip() or None
        category = request.POST.get("category", "Furniture")
        region = request.POST.get("region", "Harare")
        department = request.POST.get("department", "Administration")
        condition = request.POST.get("condition") or request.POST.get("state", "Good")
        assigned_to = request.POST.get("assigned_to") or request.POST.get("user_name")
        office_number = request.POST.get("office_number")
        
        # Physical Location Foreign Key lookup
        location_id = request.POST.get("current_location")
        location_obj = Location.objects.filter(id=location_id).first() if location_id else None
        
        purchase_date = request.POST.get("purchase_date") or None
        checked_by = request.POST.get("checked_by")
        date_checked = request.POST.get("date_checked") or None

        Asset.objects.create(
            name=name,
            asset_tag=asset_tag,
            serial_number=serial_number,
            category=category,
            region=region,
            department=department,
            condition=condition,
            assigned_to=assigned_to,
            current_location=location_obj,
            office_number=office_number,
            purchase_date=purchase_date if purchase_date else None,
            checked_by=checked_by,
            date_checked=date_checked if date_checked else None,
        )
        return redirect("assets:asset_sync_workspace")

    locations = Location.objects.all()
    return render(
        request, 
        "assets/asset_add.html", 
        {
            "locations": locations,
            "region_choices": Asset.REGION_CHOICES,
            "department_choices": Asset.DEPARTMENT_CHOICES,
            "category_choices": Asset.CATEGORY_CHOICES,
            "condition_choices": Asset.CONDITION_CHOICES,
        }
    )


def asset_edit(request, asset_id):
    """Edit an existing asset record including region, serial number, department, and location."""
    asset = get_object_or_404(Asset, id=asset_id)

    if request.method == "POST":
        asset.name = request.POST.get("name") or request.POST.get("description", asset.name)
        asset.asset_tag = request.POST.get("asset_tag") or request.POST.get("asset_number", asset.asset_tag)
        asset.serial_number = request.POST.get("serial_number", "").strip() or None
        asset.category = request.POST.get("category", asset.category)
        asset.region = request.POST.get("region", asset.region)
        asset.department = request.POST.get("department", asset.department)
        asset.condition = request.POST.get("condition") or request.POST.get("state", asset.condition)
        asset.assigned_to = request.POST.get("assigned_to") or request.POST.get("user_name", asset.assigned_to)
        asset.office_number = request.POST.get("office_number", asset.office_number)
        
        location_id = request.POST.get("current_location")
        if location_id:
            asset.current_location = Location.objects.filter(id=location_id).first()
        elif "current_location" in request.POST and not location_id:
            asset.current_location = None

        purchase_date = request.POST.get("purchase_date")
        if purchase_date:
            asset.purchase_date = purchase_date
            
        asset.checked_by = request.POST.get("checked_by", asset.checked_by)
        
        date_checked = request.POST.get("date_checked")
        if date_checked:
            asset.date_checked = date_checked

        asset.save()
        return redirect("assets:asset_sync_workspace")

    locations = Location.objects.all()
    return render(
        request, 
        "assets/asset_edit.html", 
        {
            "asset": asset, 
            "locations": locations,
            "region_choices": Asset.REGION_CHOICES,
            "department_choices": Asset.DEPARTMENT_CHOICES,
            "category_choices": Asset.CATEGORY_CHOICES,
            "condition_choices": Asset.CONDITION_CHOICES,
        }
    )


def asset_delete(request, asset_id):
    """Delete an asset record."""
    asset = get_object_or_404(Asset, id=asset_id)
    asset.delete()
    return redirect("assets:asset_sync_workspace")


def asset_transfer(request, asset_id=None):
    """Render and handle asset movement / transfer logic including region, department, and location updates."""
    selected_asset = None
    if asset_id:
        selected_asset = get_object_or_404(Asset, id=asset_id)

    if request.method == "POST":
        target_asset_id = request.POST.get("asset_id")
        asset = get_object_or_404(Asset, id=target_asset_id)
        
        to_region = request.POST.get("to_region") or asset.region
        to_department = request.POST.get("to_department") or asset.department
        to_person = request.POST.get("to_person") or asset.assigned_to
        to_office = request.POST.get("to_office") or asset.office_number
        to_location_id = request.POST.get("to_location")
        to_location_obj = Location.objects.filter(id=to_location_id).first() if to_location_id else asset.current_location
        reason = request.POST.get("reason")

        AssetTransfer.objects.create(
            asset=asset,
            from_region=asset.region,
            from_department=asset.department,
            from_location=asset.current_location,
            from_office=asset.office_number,
            from_person=asset.assigned_to,
            to_region=to_region,
            to_department=to_department,
            to_location=to_location_obj,
            to_office=to_office,
            to_person=to_person,
            reason=reason,
            transferred_by=request.user if request.user.is_authenticated else None
        )

        return redirect("assets:asset_sync_workspace")

    assets = Asset.objects.all().order_by('name')
    locations = Location.objects.all()
    return render(
        request, 
        "assets/asset_transfer.html", 
        {
            "assets": assets,
            "locations": locations,
            "selected_asset": selected_asset,
            "region_choices": Asset.REGION_CHOICES,
            "department_choices": Asset.DEPARTMENT_CHOICES,
        }
    )


def asset_export_csv(request):
    """Exports all asset audit records including Region and Serial Number to a downloadable CSV file."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ZESA_Asset_Inventory_Audit.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Asset Tag', 
        'Serial Number',
        'Description / Item Name', 
        'Region',
        'Department / Unit',
        'Category',
        'Audited Office No',
        'Physical Location / Building',
        'Condition / State', 
        'Custodian / User', 
        'Checked By', 
        'Date Checked'
    ])

    assets = Asset.objects.select_related('current_location').all().order_by('-id')
    for asset in assets:
        loc_str = str(asset.current_location) if asset.current_location else '-'
        writer.writerow([
            asset.asset_tag or '-',
            asset.serial_number or '-',
            asset.name or '-',
            asset.region or 'Harare',
            asset.department or 'Administration',
            asset.category or 'Furniture',
            asset.office_number or '-',
            loc_str,
            asset.condition or 'Good',
            asset.assigned_to or '-',
            asset.checked_by or '-',
            asset.date_checked or asset.purchase_date or '-'
        ])

    return response


def generate_pdf_report(request):
    """Generates a downloadable/viewable PDF Asset Audit Report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=15
    )
    
    elements.append(Paragraph("Zimbabwe Electricity Supply Authority", title_style))
    elements.append(Paragraph("Asset Inventory & Movement Audit Report", subtitle_style))
    elements.append(Spacer(1, 10))

    table_data = [[
        'Asset Tag',
        'Serial No',
        'Description',
        'Region',
        'Department',
        'State', 
        'Office No', 
        'Custodian', 
        'Checked By', 
        'Date'
    ]]

    assets = Asset.objects.all().order_by('-id')
    cell_style = ParagraphStyle('CellText', parent=styles['Normal'], fontSize=8, leading=10)

    for asset in assets:
        table_data.append([
            Paragraph(asset.asset_tag or '-', cell_style),
            Paragraph(asset.serial_number or '-', cell_style),
            Paragraph(asset.name or '-', cell_style),
            Paragraph(asset.region or '-', cell_style),
            Paragraph(asset.department or 'Administration', cell_style),
            Paragraph(asset.condition or 'Good', cell_style),
            Paragraph(asset.office_number or '-', cell_style),
            Paragraph(asset.assigned_to or '-', cell_style),
            Paragraph(asset.checked_by or '-', cell_style),
            Paragraph(str(asset.date_checked or asset.purchase_date or '-'), cell_style)
        ])

    col_widths = [75, 75, 120, 70, 80, 50, 60, 90, 80, 70]
    
    asset_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    asset_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))

    elements.append(asset_table)
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="ZESA_Asset_Audit_Report.pdf"'
    return response


def reports_dashboard(request):
    """Main Reports Hub rendering summary statistics and quick report links."""
    total_assets = Asset.objects.count()
    
    region_counts = Asset.objects.values('region').annotate(total=Count('region'))
    condition_counts = Asset.objects.values('condition').annotate(total=Count('condition'))
    department_counts = Asset.objects.values('department').annotate(total=Count('department')).order_by('-total')
    office_counts = Asset.objects.values('office_number').annotate(total=Count('office_number')).order_by('-total')[:5]
    recent_transfers = AssetTransfer.objects.select_related('asset').order_by('-id')[:10]

    return render(request, 'assets/reports.html', {
        'total_assets': total_assets,
        'region_counts': region_counts,
        'condition_counts': condition_counts,
        'department_counts': department_counts,
        'office_counts': office_counts,
        'recent_transfers': recent_transfers,
    })


def transfer_history_report(request):
    """Detailed audit log report for all asset movement/transfers."""
    transfers = AssetTransfer.objects.select_related('asset').all().order_by('-id')
    return render(request, 'assets/report_transfers.html', {'transfers': transfers})


# Alias to resolve potential url mapping mismatches
reports = reports_dashboard