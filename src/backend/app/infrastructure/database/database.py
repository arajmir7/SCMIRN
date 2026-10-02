"""
Database initialization and session management.
"""

import os
from flask import Flask
from sqlalchemy import inspect

from app.extensions import db


def init_database(app: Flask) -> None:
    """
    Initialize database with app context.
    Creates tables if they don't exist.
    """
    with app.app_context():
        # Import models to register them with SQLAlchemy
        from .models import (
            IssueORM,
            UserORM,
            DocumentORM,
            OfficeORM,
            ChatLogORM,
            IoTAssetORM,
            IoTReadingORM,
            BlockchainTransactionORM,
            UserGamificationORM,
            ResilienceHubORM,
            SRSIssueORM,
            SRSIssueEventORM,
            SRSWorkOrderORM,
            SRSContractorORM,
            SRSAssetORM,
            SRSUtilityMapORM,
            SRSBudgetEventORM,
            SRSAuditLogORM,
        )
        from app.source_routing.models import (
            OfficialSource,
            Authority,
            GovernmentService,
            RouteRule,
            RouteDecision,
        )
        from app.source_routing.audit_models import AuditEvent
        from app.staff_auth.models import (
            Tenant, StaffUser, StaffMfaFactor, StaffMfaChallenge,
            StaffRoleGrant, StaffSession, StaffCase, StaffCaseEvent,
            StaffAuditEvent,
        )
        
        # Development/test databases may be initialized automatically. A
        # production database must be migrated by an explicit operator job.
        if app.config.get('AUTO_CREATE_DB', True):
            db.create_all()
        elif app.config.get('SCMIRN_ENVIRONMENT') == 'production' and not app.config.get('MIGRATION_MODE', False):
            inspector = inspect(db.engine)
            required_tables = sorted(db.metadata.tables)
            missing = [name for name in required_tables if not inspector.has_table(name)]
            if missing:
                raise RuntimeError('Production database schema is not prepared; missing mapped tables: ' + ', '.join(missing))
            from .security import validate_production_runtime_role
            with db.engine.connect() as connection:
                validate_production_runtime_role(
                    connection,
                    expected_role=app.config.get('SCMIRN_APP_DB_ROLE', 'scmirn_app'),
                    staff_api_enabled=app.config.get(
                        'STAFF_API_ENABLED', app.config.get('STAFF_AUTH_ENABLED', False)
                    ),
                )

        if app.config.get('AUTO_SEED_ROUTING_REGISTRY'):
            from app.source_routing.registry_seed import seed_routing_registry
            seed_routing_registry()
        
        app.logger.info("Database initialized")


def seed_database() -> None:
    """
    Seed database with sample data for demonstration.
    """
    from app.extensions import db
    from .models import IssueORM, OfficeORM
    from .repositories import SQLAlchemyIssueRepository
    from app.core.entities.issue import Issue, Location, PriorityTier, IssueStatus, MediaFile
    import json
    import hashlib
    import random
    
    # Check if already seeded
    if IssueORM.query.first():
        print("Database already seeded")
        return
    
    # Sample issues with real Unsplash images
    sample_issues = [
        {
            'title': 'Critical: Deep Pothole on Ring Road near AIIMS Flyover',
            'description': 'Dangerous 4-foot wide pothole on AIIMS Flyover, Ring Road. Daily accidents reported. Exact location: 200m before Safdarjung Hospital crossing towards Dhaula Kuan.',
            'category': 'road',
            'priority_score': 9800,
            'priority_tier': 'critical',
            'lat': 28.5672,
            'lon': 77.2100,
            'fund_target': 75000,
            'fund_collected': 32000,
            'status': 'verified',
            'photo': 'https://images.unsplash.com/photo-1565130054090-5b9231d55db7?w=800&q=80',
            'ai_confidence': 0.97,
            'landmarks': 'AIIMS, Safdarjung Hospital, Ring Road'
        },
        {
            'title': 'Severe Water Logging at ITO Crossing - Daily Traffic Jam',
            'description': 'Chronic flooding at ITO intersection during monsoon. Water depth 2-3 feet. Affects Vikas Marg, Bahadur Shah Zafar Marg, and Ring Road. Exact: Under ITO Metro Station.',
            'category': 'water',
            'priority_score': 9600,
            'priority_tier': 'critical',
            'lat': 28.6280,
            'lon': 77.2410,
            'fund_target': 120000,
            'fund_collected': 45000,
            'status': 'in_progress',
            'photo': 'https://images.unsplash.com/photo-1581093458791-9f3c3900df4b?w=800&q=80',
            'ai_confidence': 0.96,
            'landmarks': 'ITO Metro, Delhi High Court, Vikas Marg'
        },
        {
            'title': 'Broken Street Lights on Lodhi Road - Khan Market Stretch',
            'description': 'Complete darkness on Lodhi Road from Aga Khan Hall to India Habitat Centre. 15+ lights non-functional. High security zone with embassies. Women safety risk.',
            'category': 'safety',
            'priority_score': 9200,
            'priority_tier': 'high',
            'lat': 28.5916,
            'lon': 77.2197,
            'fund_target': 45000,
            'fund_collected': 45000,
            'status': 'funded',
            'photo': 'https://images.unsplash.com/photo-1516455590571-18256e5bb9ff?w=800&q=80',
            'ai_confidence': 0.95,
            'landmarks': 'Lodhi Garden, India Habitat Centre, Khan Market'
        },
        {
            'title': 'Open Manhole on Outer Ring Road near Mukherjee Nagar',
            'description': 'Uncovered sewer manhole on Outer Ring Road, 100m from Batra Cinema towards Model Town. Multiple vehicle incidents. Risk to 2-wheelers.',
            'category': 'road',
            'priority_score': 9400,
            'priority_tier': 'critical',
            'lat': 28.7021,
            'lon': 77.2020,
            'fund_target': 25000,
            'fund_collected': 8000,
            'status': 'reported',
            'photo': 'https://images.unsplash.com/photo-1621905252507-b35492b9c75e?w=800&q=80',
            'ai_confidence': 0.96,
            'landmarks': 'Batra Cinema, Mukherjee Nagar, GTB Nagar Metro'
        },
        {
            'title': 'Illegal Encroachment on Main Road - Lajpat Nagar Market',
            'description': 'Permanent shop extensions blocking 40% of road width on Lajpat Nagar Central Market main road. Fire hazard and traffic congestion. Exact: Near Lajpat Nagar Metro Gate 2.',
            'category': 'road',
            'priority_score': 8800,
            'priority_tier': 'high',
            'lat': 28.5639,
            'lon': 77.2421,
            'fund_target': 60000,
            'fund_collected': 15000,
            'status': 'verified',
            'photo': 'https://images.unsplash.com/photo-1530587191325-3db32d826c18?w=800&q=80',
            'ai_confidence': 0.93,
            'landmarks': 'Lajpat Nagar Metro, Central Market, Amar Colony'
        }
    ]
    
    # Create issue ORMs
    import uuid
    for issue_data in sample_issues:
        issue_orm = IssueORM(
            public_id=str(uuid.uuid4())[:8],
            title=issue_data['title'],
            description=issue_data['description'],
            category=issue_data['category'],
            priority_score=issue_data['priority_score'],
            priority_tier=issue_data['priority_tier'],
            lat=issue_data['lat'],
            lon=issue_data['lon'],
            fund_target=issue_data['fund_target'],
            fund_collected=issue_data['fund_collected'],
            status=issue_data['status'],
            media_files=json.dumps([issue_data['photo']]),
            integrity_hash=hashlib.sha256(issue_data['title'].encode()).hexdigest(),
            ai_confidence=issue_data['ai_confidence'],
            location_landmarks=issue_data.get('landmarks', '')
        )
        db.session.add(issue_orm)
    
    # Seed offices
    offices = [
        {
            'name': 'PWD Office (Roads)',
            'department': 'Public Works Dept',
            'address': '2nd Floor, Palika Bhawan, RK Puram Sector 12, New Delhi - 110022',
            'lat': 28.5744,
            'lon': 77.1758,
            'officer_name': 'Er. Rajinder Kumar',
            'phone': '011-26175559',
            'timings': '10:00 AM - 5:30 PM',
            'services': 'Road repair, Drainage, Street lights',
            'rating': 4.1
        },
        {
            'name': 'MCD Headquarters',
            'department': 'Municipal Corporation',
            'address': 'MCD Civic Centre, Minto Road, New Delhi - 110002',
            'lat': 28.6329,
            'lon': 77.2215,
            'officer_name': 'Commissioner Gyanesh Bharti',
            'phone': '011-23230131',
            'timings': '9:30 AM - 6:00 PM',
            'services': 'Sanitation, Garbage, Road maintenance',
            'rating': 3.9
        },
        {
            'name': 'DJB Office (Water)',
            'department': 'Delhi Jal Board',
            'address': 'Varunalaya Phase-II, Karol Bagh, New Delhi - 110005',
            'lat': 28.6521,
            'lon': 77.1937,
            'officer_name': 'Sh. Satyendar Jain',
            'phone': '011-23538185',
            'timings': '10:00 AM - 5:00 PM',
            'services': 'Water supply, Sewerage, Billing disputes',
            'rating': 4.0
        },
        {
            'name': 'BSES Rajdhani',
            'department': 'Electricity',
            'address': 'BSES Bhawan, Nehru Place, New Delhi - 110019',
            'lat': 28.5494,
            'lon': 77.2512,
            'officer_name': 'Customer Care',
            'phone': '39999707',
            'timings': '24x7',
            'services': 'New connections, Power cuts, Bill complaints',
            'rating': 4.2
        },
        {
            'name': 'DCP Traffic (South)',
            'department': 'Delhi Police',
            'address': 'Traffic Police HQ, Todarpur Road, Delhi Cantt - 110010',
            'lat': 28.5708,
            'lon': 77.1596,
            'officer_name': 'DCP South',
            'phone': '011-26851578',
            'timings': '24x7',
            'services': 'Traffic issues, Accident reports, Challan disputes',
            'rating': 4.3
        }
    ]
    
    for office_data in offices:
        office = OfficeORM(**office_data)
        db.session.add(office)
    
    db.session.commit()
    print(f"✅ Seeded {len(sample_issues)} issues and {len(offices)} offices")
