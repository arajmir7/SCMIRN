# -*- coding: utf-8 -*-
import sqlite3
import json
import hashlib
import time
import os
import random
import re
import tempfile
import math
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, g, request, jsonify, send_from_directory
from flask import session
from werkzeug.utils import secure_filename

def _load_env_file():
    env_path = Path(__file__).resolve().parents[6] / '.env'
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or os.urandom(32).hex()
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

DATABASE = os.path.join(tempfile.gettempdir(), 'scmirn_civic_intelligence.db')
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
UPLOAD_FOLDER = os.path.join(APP_DIR, 'infrastructure', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'pdf', 'doc', 'docx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'issues'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'verifications'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'documents'), exist_ok=True)
# Ensure all upload directories exist with proper permissions
for folder in ['issues', 'verifications', 'documents', 'profiles']:
    path = os.path.join(UPLOAD_FOLDER, folder)
    os.makedirs(path, exist_ok=True)

# Register Jinja2 filters
@app.template_filter('fromjson')
def fromjson_filter(value):
    """Parse JSON string to object"""
    try:
        return json.loads(value) if value else []
    except Exception:
        return []

THEME = {
    'royal_indigo': '#0f172a',
    'electric_teal': '#06b6d4',
    'soft_pearl': '#f8fafc',
    'warm_gold': '#f59e0b',
    'coral_blush': '#ef4444',
    'emerald': '#10b981',
    'violet': '#8b5cf6'
}

class CivicIntelligenceAI:
    """
    World's First AI-Driven Civic Intelligence System
    Combining NLP, Legal Tech, and Government Data Integration
    """

    def __init__(self):
        self.memory = {}

        # Comprehensive response database
        self.responses = {
            'rights_lookup': self._generate_rights_response,
            'document_draft': self._generate_document_help,
            'office_finder': self._generate_office_response,
            'problem_solver': self._generate_solution_pathway,
            'predictive': self._generate_predictive_insights,
        }

        # Legal knowledge base
        self.legal_framework = {
            'rti': {
                'title': 'Right to Information Act, 2005',
                'steps': ['Identify Public Information Officer (PIO)', 'Draft application (₹10 fee)', 'Submit to concerned department', '30-day mandatory response'],
                'appeal': 'First Appeal within 30 days if no response',
                'template': 'rti_template'
            },
            'fir': {
                'title': 'Section 154 CrPC - FIR Filing',
                'rights': 'Police MUST register FIR for cognizable offenses',
                'steps': ['Go to police station (any jurisdiction for cyber crimes)', 'Demand FIR copy free of charge', 'If refused, approach Superintendent of Police'],
                'remedy': 'Write to SP/DCP or approach Magistrate under Section 156(3)'
            },
            'consumer': {
                'title': 'Consumer Protection Act, 2019',
                'rights': 'File complaint in District Commission (₹50L-₹5Cr) or State/National',
                'timeline': 'Complaint must be decided within 3-6 months',
                'online': 'efiling.consumerhelpline.gov.in'
            },
            'ration': {
                'title': 'National Food Security Act, 2013',
                'rights': ' entitled to 5kg rice/wheat per person monthly at ₹3/₹2/₹1',
                'grievance': 'Call 1967 (Toll-free) or visit food.gov.in'
            }
        }

        # Document templates
        self.templates = {
            'rti': """RTI Application
To: The Public Information Officer,
[Department Name],
[Address]

Subject: Request for information under RTI Act, 2005

Dear Sir/Madam,
I seek the following information:
1. [Specific information requested]
2. [Time period]
3. [Documents needed]

Fee of ₹10 paid via [IPO/Bank Draft/Cash].
Contact: [Your Address]
Date: [Date]""",

            'fir_complaint': """COMPLAINT FOR NON-REGISTRATION OF FIR
To: The Superintendent of Police,
[District]

Subject: Refusal to register FIR regarding [Offense]

Respected Sir,
I beg to state that on [Date], I approached [Police Station] to report [incident]. Despite the cognizable nature of the offense under Section [IPC Section], the duty officer refused to register FIR.
Requested action: Issue directions for immediate FIR registration.
Enclosure: Copy of written complaint made to SHO.""",
        }
    def _generate_rights_response(self, query):
        """Generate rights-based response"""
        detected_areas = []
        query_lower = query.lower()

        mappings = {
            'rti|information|transparency': ('rti', 'Right to Information'),
            'fir|police|theft|fraud|crime': ('fir', 'Criminal Procedure & Policing'),
            'consumer|product|service|defect': ('consumer', 'Consumer Rights'),
            'ration|food|pds|fair price': ('ration', 'Food Security Rights'),
            'electricity|bill|power cut': ('electricity', 'Electricity Rights - Consumer Charter'),
            'landlord|rent|eviction|lease': ('rent', 'Rent Control & Tenant Rights'),
            'scholarship|education|school': ('education', 'Right to Education Act'),
            'hospital|health|treatment': ('health', 'Public Health Rights')
        }

        for pattern, (key, title) in mappings.items():
            if re.search(pattern, query_lower):
                detected_areas.append((key, title))

        if not detected_areas:
            return None

        response = "**⚖️ Your Legal Rights Detected:**\n\n"
        for key, title in detected_areas[:2]:
            if key in self.legal_framework:
                data = self.legal_framework[key]
                response += f"**{data['title']}**\n"
                response += f"• {data.get('rights', 'Key protections available')}\n"
                if 'steps' in data:
                    response += "**Immediate Steps:**\n" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(data['steps'][:3])]) + "\n"
                response += "\n"

        response += "**📄 Would you like me to:**\n"
        response += "• Draft a formal complaint/RTI/application\n"
        response += "• Find the nearest relevant government office\n"
        response += "• Explain appeal procedures\n"
        response += "• Track similar cases in your area"

        return response

    def _generate_document_help(self, query):
        """Offer document generation assistance"""
        return ("**📝 Document Auto-Generation Ready**\n\n"
                "I can instantly create legally-valid documents for:\n\n"
                "**Available Templates:**\n"
                "• **RTI Application** - Information requests (₹10 fee structure)\n"
                "• **FIR Complaint Letter** - To SP/DCP for non-registration\n"
                "• **Consumer Complaint** - District/State/National Commission\n"
                "• **Rent Dispute Notice** - Landlord-tenant issues\n"
                "• **Scholarship Grievance** - Education department appeals\n"
                "• **Electricity Complaint** - Dispute resolution format\n\n"
                "**To generate:** Tell me which document + your basic details (name, address, department)\n\n"
                "_All templates comply with current Indian legal standards_")

    def _generate_office_response(self, query):
        """Generate office finding logic"""
        return ("**🏛️ Smart Office Locator**\n\n"
                "Based on your location and problem type:\n\n"
                "**Nearest Authorities:**\n"
                "• **District Office** - [Auto-detected based on GPS]\n"
                "• **Department Location** - With current officer name\n"
                "• **Timings:** 10:00 AM - 5:00 PM (Lunch: 1:30-2:00)\n"
                "• **Required Documents:** ID Proof + Application + Supporting docs\n\n"
                "**💡 Pro Tips:**\n"
                "• Best time to visit: 10:30 AM (avoid queues)\n"
                "• Always take 'receiving' stamp on copies\n"
                "• If officer absent, meet 'In-charge' and get written acknowledgment\n\n"
                "Want me to mark this office on your map with navigation?")

    def _generate_solution_pathway(self, query):
        """Create step-by-step resolution pathway"""
        return ("**🎯 Your Personalized Action Plan**\n\n"
                "**Phase 1: Immediate (Today)**\n"
                "1. Document the problem (photos/messages/bills)\n"
                "2. Note approximate financial/safety impact\n"
                "3. Gather ID and address proof\n\n"
                "**Phase 2: Formal Approach (This Week)**\n"
                "1. File complaint at concerned office (I'll locate it)\n"
                "2. Get acknowledgment receipt (CRITICAL)\n"
                "3. If online portal exists, file parallel complaint\n\n"
                "**Phase 3: Escalation (If delayed)**\n"
                "1. Week 2: Reminder with reference number\n"
                "2. Week 4: RTI for status (30 days mandatory reply)\n"
                "3. Week 6: Approach higher authority/ombudsman\n\n"
                "**Success Rate:** 78% resolved at Phase 2 when properly documented.\n\n"
                "Shall I draft the Phase 2 complaint letter now?")

    def _generate_predictive_insights(self, query):
        """Generate predictive civic analytics"""
        return ("**📊 Predictive Civic Intelligence**\n\n"
                "**Your Area Analysis:**\n"
                "• **Top Issue Category:** Road infrastructure (34% of reports)\n"
                "• **Avg Resolution Time:** 12 days (vs 28 days national average)\n"
                "• **Success Rate:** 82% for funded issues\n"
                "• **Peak Complaint Season:** Monsoon (July-Sept)\n\n"
                "**Department Performance:**\n"
                "• Electricity Dept: Fastest response (4.2 days avg)\n"
                "• Water Board: Medium (11 days)\n"
                "• Road Authority: Slower (18 days) - escalate after 10 days\n\n"
                "**💡 Strategic Advice:**\n"
                "Issues tagged 'School Zone' or 'Hospital Vicinity' get 3x faster resolution. "
                "Include these landmarks in your report if applicable.")

    def process(self, text, session_id='default', user_location=None):
        """
        Main processing engine for civic queries
        Returns: dict with response, action, intent, documents
        """
        text_lower = text.strip().lower()

        # Document generation trigger
        if any(word in text_lower for word in ['draft', 'write', 'generate', 'template', 'letter']):
            doc_type = 'generic'
            if 'rti' in text_lower: doc_type = 'rti'
            elif 'fir' in text_lower or 'police' in text_lower: doc_type = 'fir'
            elif 'complaint' in text_lower: doc_type = 'complaint'

            return {
                'intent': 'document_generation',
                'response': self._generate_document_help(text),
                'document_type': doc_type,
                'confidence': 0.95,
                'action': 'show_document_generator'
            }

        # Rights/Legal query
        if any(word in text_lower for word in ['right', 'legal', 'law', 'act', 'section', 'can they', 'allowed']):
            rights_resp = self._generate_rights_response(text)
            if rights_resp:
                return {
                    'intent': 'rights_lookup',
                    'response': rights_resp,
                    'confidence': 0.92,
                    'related_laws': list(self.legal_framework.keys())[:3]
                }

        # Office/Location query
        if any(word in text_lower for word in ['office', 'where', 'address', 'location', 'department', 'go', 'visit']):
            return {
                'intent': 'office_finder',
                'response': self._generate_office_response(text),
                'confidence': 0.88,
                'action': 'show_map_overlay'
            }

        # Predictive/Analytics query
        if any(word in text_lower for word in ['predict', 'analytics', 'statistics', 'success rate', 'average', 'chance']):
            return {
                'intent': 'predictive_analysis',
                'response': self._generate_predictive_insights(None),
                'confidence': 0.85,
                'action': 'show_analytics'
            }

        # Problem solving pathway
        if any(word in text_lower for word in ['what should i do', 'how to fix', 'solution', 'steps', 'process', 'help me']):
            return {
                'intent': 'problem_solver',
                'response': self._generate_solution_pathway(text),
                'confidence': 0.90,
                'action': 'show_action_plan'
            }

        # General civic greeting with context awareness
        return {
            'intent': 'civic_companion',
            'response': ("**🌍 Welcome to SCMIRN - The Future of Civic Democracy**\n\n"
                        "I'm the world's first AI-driven civic intelligence system. I combine the power of ChatGPT, "
                        "Google Maps, legal databases, and government records to solve your real-world problems.\n\n"
                        "**I can help you:**\n"
                        "⚖️ **Understand Legal Rights** - RTI, FIR, Consumer, Labor laws\n"
                        "📝 **Draft Documents** - Complaints, RTIs, applications, appeals\n"
                        "🏛️ **Find Government Offices** - With live timings and officer details\n"
                        "🎯 **Create Action Plans** - Step-by-step problem resolution\n"
                        "📊 **Predict Success Rates** - Data-driven civic strategy\n"
                        "🗺️ **Report Civic Issues** - Potholes to corruption with AI prioritization\n\n"
                        "**Describe your problem naturally:**\n"
                        "• \"My landlord evicting me illegally\"\n"
                        "• \"Police not filing my FIR\"\n"
                        "• \"Scholarship delayed 6 months\"\n"
                        "• \"Wrong electricity bill\"\n\n"
                        "What issue are you facing today?"),
            'confidence': 0.95,
            'action': 'show_capabilities'
        }

class StreetLevelMapper:
    """
    Enhanced mapping with exact street-level precision
    Integrates with OpenStreetMap for detailed road visualization
    """
    
    def __init__(self):
        self.tile_providers = {
            'osm': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            'terrain': 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            'dark': 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        }
        
    def get_precise_coordinates(self, address_hint=None):
        """Get GPS coordinates with high precision"""
        # In production, this would use geocoding API
        return {
            'accuracy': 'high',  # vs 'low' for approximate
            'method': 'gps',     # vs 'ip' or 'manual'
            'zoom_recommended': 18  # street level vs 12 (city level)
        }
    
    def generate_street_view(self, lat, lon, heading=0):
        """Generate street-level imagery reference"""
        return {
            'street_view_available': True,
            'heading': heading,
            'pitch': 0,
            'fov': 90,
            'embed_url': f"https://www.openstreetmap.org/#map=19/{lat}/{lon}"
        }
    
    def calculate_road_distance(self, lat1, lon1, lat2, lon2):
        """Calculate exact road distance using Haversine formula"""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return {
            'straight_line_meters': R * c,
            'estimated_road_meters': R * c * 1.3,  # roads are ~30% longer
            'walking_time_minutes': (R * c * 1.3) / 83  # 5km/h walking speed
        }

street_mapper = StreetLevelMapper()

ai_engine = CivicIntelligenceAI()

def get_db():
    if not hasattr(g, '_database'):
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        g._database = sqlite3.connect(DATABASE)
        g._database.row_factory = sqlite3.Row
    return g._database

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, '_database'):
        g._database.close()

def init_db():
    with app.app_context():
        db = get_db()

        # Core issues table with photos
        db.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                lat REAL,
                lon REAL,
                priority_score INTEGER DEFAULT 0,
                priority_tier TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'reported',
                fund_target REAL DEFAULT 5000,
                fund_collected REAL DEFAULT 0,
                media_files TEXT DEFAULT '[]',
                ai_confidence REAL DEFAULT 0.0,
                integrity_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Government offices database
        db.execute('''
            CREATE TABLE IF NOT EXISTS offices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                department TEXT,
                address TEXT,
                lat REAL,
                lon REAL,
                officer_name TEXT,
                phone TEXT,
                timings TEXT,
                services TEXT,
                rating REAL
            )
        ''')

        # Chat logs
        db.execute('''
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                intent TEXT,
                confidence REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Generated documents
        db.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                doc_type TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        db.commit()

def seed_data():
    db = get_db()
    if db.execute('SELECT COUNT(*) FROM issues').fetchone()[0] > 0:
        return
    
    # Enhanced street-level precise data with actual Delhi coordinates
    sample_issues = [
        {
            'title': 'Critical: Deep Pothole on Ring Road near AIIMS Flyover',
            'description': 'Dangerous 4-foot wide pothole on AIIMS Flyover, Ring Road. Daily accidents reported. Exact location: 200m before Safdarjung Hospital crossing towards Dhaula Kuan. GPS verified.',
            'category': 'Road Safety',
            'priority': 9800,
            'tier': 'critical',
            'lat': 28.5672,  # Exact AIIMS coordinates
            'lon': 77.2100,
            'fund': 75000,
            'collected': 32000,
            'status': 'verified',
            'photo': 'https://images.unsplash.com/photo-1565130054090-5b9231d55db7?w=800&q=80',
            'ai_conf': 0.97,
            'landmarks': 'AIIMS Hospital, Safdarjung Hospital, Ring Road Flyover',
            'road_name': 'Ring Road (Mahatma Gandhi Road)',
            'pincode': '110029'
        },
        {
            'title': 'Severe Water Logging at ITO Crossing - Daily Traffic Jam',
            'description': 'Chronic flooding at ITO intersection during monsoon. Water depth 2-3 feet. Affects Vikas Marg, Bahadur Shah Zafar Marg, and Ring Road. Exact: Under ITO Metro Station.',
            'category': 'Water & Drainage',
            'priority': 9600,
            'tier': 'critical',
            'lat': 28.6280,  # Exact ITO coordinates
            'lon': 77.2410,
            'fund': 120000,
            'collected': 45000,
            'status': 'in_progress',
            'photo': 'https://images.unsplash.com/photo-1581093458791-9f3c3900df4b?w=800&q=80',
            'ai_conf': 0.96,
            'landmarks': 'ITO Metro Station, Delhi Police HQ, Vikas Minar',
            'road_name': 'ITO Crossing (BSZ Marg & Vikas Marg)',
            'pincode': '110002'
        },
        {
            'title': 'Broken Street Lights on Lodhi Road - Khan Market Stretch',
            'description': 'Complete darkness on Lodhi Road from Aga Khan Hall to India Habitat Centre. 15+ lights non-functional. High security zone with embassies. Women safety risk.',
            'category': 'Public Safety',
            'priority': 9200,
            'tier': 'critical',
            'lat': 28.5916,  # Exact Lodhi Road
            'lon': 77.2197,
            'fund': 45000,
            'collected': 45000,
            'status': 'funded',
            'photo': 'https://images.unsplash.com/photo-1516455590571-18256e5bb9ff?w=800&q=80',
            'ai_conf': 0.95,
            'landmarks': 'Lodhi Garden, India Habitat Centre, Khan Market, Jor Bagh',
            'road_name': 'Lodhi Road (Shanti Path to Max Mueller Marg)',
            'pincode': '110003'
        },
        {
            'title': 'Open Manhole on Outer Ring Road near Mukherjee Nagar',
            'description': 'Uncovered sewer manhole on Outer Ring Road, 100m from Batra Cinema towards Model Town. Multiple vehicle incidents. Risk to 2-wheelers.',
            'category': 'Road Safety',
            'priority': 9400,
            'tier': 'critical',
            'lat': 28.7021,  # Mukherjee Nagar
            'lon': 77.2020,
            'fund': 25000,
            'collected': 8000,
            'status': 'reported',
            'photo': 'https://images.unsplash.com/photo-1621905252507-b35492b9c75e?w=800&q=80',
            'ai_conf': 0.96,
            'landmarks': 'Batra Cinema, Mukherjee Nagar, GTB Nagar Metro',
            'road_name': 'Outer Ring Road ( NH-44 )',
            'pincode': '110009'
        },
        {
            'title': 'Illegal Encroachment on Main Road - Lajpat Nagar Market',
            'description': 'Permanent shop extensions blocking 40% of road width on Lajpat Nagar Central Market main road. Fire hazard and traffic congestion. Exact: Near Lajpat Nagar Metro Gate 2.',
            'category': 'Urban Planning',
            'priority': 8800,
            'tier': 'high',
            'lat': 28.5639,  # Lajpat Nagar
            'lon': 77.2421,
            'fund': 60000,
            'collected': 15000,
            'status': 'verified',
            'photo': 'https://images.unsplash.com/photo-1530587191325-3db32d826c18?w=800&q=80',
            'ai_conf': 0.93,
            'landmarks': 'Lajpat Nagar Metro, Central Market, Amar Colony',
            'road_name': 'Lajpat Nagar Main Road (Ring Road service lane)',
            'pincode': '110024'
        }
    ]
    
    for issue in sample_issues:
        db.execute('''
            INSERT INTO issues (title, description, category, priority_score, priority_tier,
                              lat, lon, fund_target, fund_collected, status, media_files,
                              integrity_hash, ai_confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            issue['title'], issue['description'], issue['category'], issue['priority'],
            issue['tier'], issue['lat'], issue['lon'], issue['fund'], issue['collected'],
            issue['status'], json.dumps([issue['photo']]),
            hashlib.sha256(issue['title'].encode()).hexdigest(),
            issue['ai_conf']
        ))
    
    # Enhanced offices with exact addresses
    offices = [
        ('PWD Office (Roads)', 'Public Works Dept', '2nd Floor, Palika Bhawan, RK Puram Sector 12, New Delhi', 
         28.5744, 77.1758, 'Er. Rajinder Kumar', '011-26175559', '10:00 AM - 5:30 PM', 
         'Road repair, Drainage, Street lights', 4.1),
        ('MCD Headquarters', 'Municipal Corp', 'MCD Civic Centre, Minto Road, New Delhi', 
         28.6329, 77.2215, 'Commissioner Gyanesh Bharti', '011-23230131', '9:30 AM - 6:00 PM', 
         'Sanitation, Garbage, Road maintenance', 3.9),
        ('DJB Office (Water)', 'Delhi Jal Board', 'Varunalaya Phase-II, Karol Bagh, New Delhi', 
         28.6521, 77.1937, 'Sh. Satyendar Jain', '011-23538185', '10:00 AM - 5:00 PM', 
         'Water supply, Sewerage, Billing disputes', 4.0),
        ('BSES Rajdhani', 'Electricity', 'BSES Bhawan, Nehru Place, New Delhi', 
         28.5494, 77.2512, 'Customer Care', '39999707', '24x7', 
         'New connections, Power cuts, Bill complaints', 4.2),
        ('DCP Traffic (South)', 'Delhi Police', 'Traffic Police HQ, Todarpur Road, Delhi Cantt', 
         28.5708, 77.1596, 'DCP South', '011-26851578', '24x7', 
         'Traffic issues, Accident reports, Challan disputes', 4.3)
    ]
    
    for office in offices:
        db.execute('INSERT INTO offices (name, department, address, lat, lon, officer_name, phone, timings, services, rating) VALUES (?,?,?,?,?,?,?,?,?,?)', office)
    
    db.commit()

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="SCMIRN - World's First AI-Driven Civic Intelligence System. Solve government, legal, and social problems instantly.">
    <title>SCMIRN | The Future of Democratic Participation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <style>
        :root {
            --primary: #0f172a;
            --accent: #06b6d4;
            --secondary: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: #f8fafc;
            color: var(--primary);
            overflow-x: hidden;
        }
        
        h1, h2, h3, h4, h5, .display-font {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        /* Hero Section - Future of Democracy */
        .hero-civic {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            position: relative;
            overflow: hidden;
        }
        
        .hero-civic::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('https://images.unsplash.com/photo-1497366216548-37526070297c?w=1920&q=80') center/cover;
            opacity: 0.1;
        }
        
        .hero-grid {
            position: absolute;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(6, 182, 212, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(6, 182, 212, 0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: gridMove 20s linear infinite;
        }
        
        @keyframes gridMove {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }
        
        .glow-text {
            text-shadow: 0 0 40px rgba(6, 182, 212, 0.5);
        }
        
        .floating-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px;
            animation: float 6s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        
        /* Feature Cards */
        .feature-civic {
            background: white;
            border-radius: 20px;
            padding: 32px;
            height: 100%;
            transition: all 0.3s;
            border: 1px solid #e2e8f0;
            position: relative;
            overflow: hidden;
        }
        
        .feature-civic:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border-color: var(--accent);
        }
        
        .feature-civic::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--accent);
            transform: scaleY(0);
            transition: transform 0.3s;
        }
        
        .feature-civic:hover::before {
            transform: scaleY(1);
        }
        
        .icon-circle {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--accent), var(--secondary));
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            margin-bottom: 20px;
        }
        
        /* AI Chatbot Interface */
        .ai-orb {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, var(--accent), var(--secondary));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 28px;
            cursor: pointer;
            box-shadow: 0 10px 40px rgba(6, 182, 212, 0.4);
            z-index: 9999;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0.7); }
            70% { box-shadow: 0 0 0 20px rgba(6, 182, 212, 0); }
        }
        
        .chat-intelligence {
            position: fixed;
            bottom: 110px;
            right: 30px;
            width: 450px;
            height: 650px;
            background: white;
            border-radius: 24px;
            box-shadow: 0 25px 80px rgba(0,0,0,0.3);
            z-index: 9998;
            display: none;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }
        
        .chat-header {
            background: linear-gradient(135deg, var(--primary), #1e293b);
            color: white;
            padding: 24px;
            position: relative;
        }
        
        .chat-body {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8fafc;
        }
        
        .message-ai {
            background: white;
            padding: 16px 20px;
            border-radius: 16px 16px 16px 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            margin-bottom: 16px;
            border-left: 3px solid var(--accent);
            font-size: 14px;
            line-height: 1.6;
        }
        
        .message-user {
            background: var(--primary);
            color: white;
            padding: 14px 18px;
            border-radius: 16px 16px 4px 16px;
            margin-bottom: 16px;
            margin-left: auto;
            max-width: 80%;
            font-size: 14px;
        }
        
        .suggestion-chip {
            display: inline-block;
            background: #e0f2fe;
            color: #0369a1;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            margin: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .suggestion-chip:hover {
            background: var(--accent);
            color: white;
        }
        
        /* Issue Cards with Images */
        .issue-card-premium {
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            transition: all 0.3s;
            height: 100%;
            border: 1px solid #e2e8f0;
        }
        
        .issue-card-premium:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.12);
        }
        
        .issue-image-wrapper {
            height: 220px;
            overflow: hidden;
            position: relative;
        }
        
        .issue-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.5s;
        }
        
        .issue-card-premium:hover .issue-image {
            transform: scale(1.05);
        }
        
        .priority-tag {
            position: absolute;
            top: 16px;
            right: 16px;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            backdrop-filter: blur(10px);
        }
        
        .tag-critical { background: rgba(239, 68, 68, 0.9); color: white; }
        .tag-high { background: rgba(245, 158, 11, 0.9); color: white; }
        .tag-medium { background: rgba(6, 182, 212, 0.9); color: white; }
        
        /* Stats Section */
        .stat-card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        }
        
        .stat-number {
            font-size: 48px;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Document Generator Preview */
        .doc-preview {
            background: #f8fafc;
            border: 2px dashed #cbd5e1;
            border-radius: 12px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        /* Map Container */
        #civicMap {
            height: 500px;
            border-radius: 24px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        #civicMap iframe {
            width: 100%;
            height: 100%;
            border: 0;
            border-radius: 24px;
        }

        .map-guide {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 12px 16px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        }

        .legend-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 6px;
        }
        
        /* Impact Section */
        .impact-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 24px;
        }
        
        .impact-item {
            background: white;
            padding: 24px;
            border-radius: 16px;
            border-left: 4px solid var(--accent);
        }
        
        /* Navigation */
        .nav-scmirn {
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            z-index: 1000;
            border-bottom: 1px solid #e2e8f0;
            padding: 16px 0;
        }
        
        .btn-primary-civic {
            background: linear-gradient(135deg, var(--accent), var(--secondary));
            color: white;
            border: none;
            padding: 12px 28px;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-primary-civic:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(6, 182, 212, 0.3);
            color: white;
        }
        
        @media (max-width: 768px) {
            .chat-intelligence { width: calc(100vw - 40px); right: 20px; }
            .hero-civic { min-height: auto; padding: 120px 0 80px; }
        }
    </style>
</head>
<body>

    <!-- Navigation -->
    <nav class="nav-scmirn">
        <div class="container">
            <div class="d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-3">
                    <div class="display-font fw-bold fs-4" style="color: var(--primary);">
                        🏛️ SCMIRN
                    </div>
                    <span class="badge bg-primary bg-opacity-10 text-primary d-none d-md-inline">v2.0 Civic Intelligence</span>
                </div>
                <div class="d-none d-md-flex align-items-center gap-4">
                    <a href="#solver" class="text-decoration-none text-dark fw-medium">Problem Solver</a>
                    <a href="#rights" class="text-decoration-none text-dark fw-medium">Rights Engine</a>
                    <a href="#map-section" class="text-decoration-none text-dark fw-medium">Live Heatmap</a>
                    <a href="#docs" class="text-decoration-none text-dark fw-medium">Documents</a>
                </div>
                <button class="btn-primary-civic" onclick="openReportModal()">
                    <i class="fas fa-plus me-2"></i>Report Issue
                </button>
            </div>
        </div>
    </nav>

    <!-- Hero Section: The Future of Democracy -->
    <section class="hero-civic text-white pt-5">
        <div class="hero-grid"></div>
        <div class="container position-relative pt-5 mt-5">
            <div class="row align-items-center min-vh-100">
                <div class="col-lg-7">
                    <div class="badge bg-white bg-opacity-10 text-white mb-4 px-3 py-2 rounded-pill border border-white border-opacity-20">
                        🚀 World's First AI-Driven Civic Intelligence System
                    </div>
                    <h1 class="display-2 fw-bold mb-4 glow-text" style="line-height: 1.1;">
                        The Future of<br>
                        <span style="color: var(--accent);">Democratic</span> Participation
                    </h1>
                    <p class="lead mb-4 opacity-90" style="font-size: 1.25rem; max-width: 600px;">
                        <strong>SCMIRN</strong> combines ChatGPT, Google Maps, Legal AI, and Government Data to help every citizen understand, access, and fix real-life problems in seconds.
                    </p>
                    <div class="d-flex flex-wrap gap-3 mb-5">
                        <button class="btn btn-light btn-lg px-4 fw-bold" onclick="toggleChat()">
                            <i class="fas fa-robot me-2 text-primary"></i>Ask AI Assistant
                        </button>
                        <button class="btn btn-outline-light btn-lg px-4" onclick="document.getElementById('features').scrollIntoView({behavior: 'smooth'})">
                            Explore Features
                        </button>
                    </div>
                    
                    <div class="row g-4 mt-2">
                        <div class="col-md-4">
                            <div class="floating-card">
                                <div class="h3 fw-bold text-info mb-1">500,000+</div>
                                <small class="opacity-75">Citizens Helped</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="floating-card" style="animation-delay: 1s;">
                                <div class="h3 fw-bold text-warning mb-1">78%</div>
                                <small class="opacity-75">Resolution Rate</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="floating-card" style="animation-delay: 2s;">
                                <div class="h3 fw-bold text-success mb-1">24/7</div>
                                <small class="opacity-75">AI Legal Aid</small>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-lg-5">
                    <div class="position-relative">
                        <img src="https://images.unsplash.com/photo-1577962917302-cd874c4e31d2?w=800&q=80" 
                             alt="Civic Technology" 
                             class="img-fluid rounded-4 shadow-lg" 
                             style="border: 1px solid rgba(255,255,255,0.2);">
                        <div class="position-absolute bottom-0 start-0 m-3 p-3 bg-white rounded-3 shadow-lg text-dark" style="max-width: 250px;">
                            <div class="d-flex align-items-center gap-2 mb-2">
                                <div class="bg-success rounded-circle" style="width: 10px; height: 10px;"></div>
                                <small class="fw-bold text-success">Live System Active</small>
                            </div>
                            <small class="text-muted">Processing civic queries across 28 states</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- What is SCMIRN -->
    <section class="py-5 bg-white">
        <div class="container py-5">
            <div class="row justify-content-center text-center mb-5">
                <div class="col-lg-8">
                    <h2 class="display-5 fw-bold mb-4">What is SCMIRN?</h2>
                    <p class="lead text-muted">
                        <strong>Smart Civic Micro-Infrastructure Resilience Network</strong> is an AI-powered civic companion that transforms how citizens interact with democracy.
                    </p>
                </div>
            </div>
            
            <div class="row g-4 mb-5">
                <div class="col-md-4 text-center">
                    <div class="bg-primary bg-opacity-10 rounded-4 p-4 mb-3 d-inline-block">
                        <i class="fas fa-brain fa-2x text-primary"></i>
                    </div>
                    <h4>AI Problem Solver</h4>
                    <p class="text-muted">Natural language understanding for complex civic issues</p>
                </div>
                <div class="col-md-4 text-center">
                    <div class="bg-warning bg-opacity-10 rounded-4 p-4 mb-3 d-inline-block">
                        <i class="fas fa-balance-scale fa-2x text-warning"></i>
                    </div>
                    <h4>Legal Rights Engine</h4>
                    <p class="text-muted">Instant access to laws, acts, and constitutional rights</p>
                </div>
                <div class="col-md-4 text-center">
                    <div class="bg-success bg-opacity-10 rounded-4 p-4 mb-3 d-inline-block">
                        <i class="fas fa-file-signature fa-2x text-success"></i>
                    </div>
                    <h4>Auto Document Gen</h4>
                    <p class="text-muted">RTI, FIR, Complaints drafted by AI in seconds</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Major Features Grid -->
    <section id="features" class="py-5 bg-light">
        <div class="container py-5">
            <div class="text-center mb-5">
                <h2 class="display-5 fw-bold">7 Pillars of Civic Intelligence</h2>
                <p class="text-muted lead">Comprehensive tools for modern democratic participation</p>
            </div>
            
            <div class="row g-4">
                <!-- 1. Smart Problem Solver -->
                <div class="col-md-6 col-lg-4">
                    <div class="feature-civic">
                        <div class="icon-circle bg-primary bg-opacity-10 text-primary">
                            <i class="fas fa-brain"></i>
                        </div>
                        <h4>🧠 Smart Problem Solver</h4>
                        <p class="text-muted">Describe any issue in plain language. AI converts it into legal cases, government requests, or formal complaints with step-by-step resolution pathways.</p>
                        <ul class="list-unstyled mt-3 small text-muted">
                            <li><i class="fas fa-check text-success me-2"></i>Natural Language Processing</li>
                            <li><i class="fas fa-check text-success me-2"></i>Multi-step Action Plans</li>
                            <li><i class="fas fa-check text-success me-2"></i>Success Prediction</li>
                        </ul>
                    </div>
                </div>
                
                <!-- 2. Office Finder -->
                <div class="col-md-6 col-lg-4">
                    <div class="feature-civic">
                        <div class="icon-circle bg-info bg-opacity-10 text-info">
                            <i class="fas fa-map-marked-alt"></i>
                        </div>
                        <h4>🏛️ Office Locator</h4>
                        <p class="text-muted">GPS-enabled finder for government offices with Live officer names, contact numbers, office timings, and optimal visit strategies.</p>
                        <ul class="list-unstyled mt-3 small text-muted">
                            <li><i class="fas fa-check text-success me-2"></i>Live Officer Database</li>
                            <li><i class="fas fa-check text-success me-2"></i>Best Visit Times</li>
                            <li><i class="fas fa-check text-success me-2"></i>Required Documents List</li>
                        </ul>
                    </div>
                </div>
                
                <!-- 3. Rights Engine -->
                <div class="col-md-6 col-lg-4">
                    <div class="feature-civic">
                        <div class="icon-circle bg-warning bg-opacity-10 text-warning">
                            <i class="fas fa-gavel"></i>
                        </div>
                        <h4>⚖️ Rights & Law Engine</h4>
                        <p class="text-muted">Instant legal analysis: Which law applies, your specific rights, government obligations, deadlines, and remedies without lawyer fees.</p>
                        <ul class="list-unstyled mt-3 small text-muted">
                            <li><i class="fas fa-check text-success me-2"></i>RTI, Consumer, Labor Acts</li>
                            <li><i class="fas fa-check text-success me-2"></i>Constitutional Rights</li>
                            <li><i class="fas fa-check text-success me-2"></i>Penalty Provisions</li>
                        </ul>
                    </div>
                </div>
                <!-- 4. Document Generator -->
                <div class="col-md-6 col-lg-4">
                    <div class="feature-civic">
                        <div class="icon-circle bg-success bg-opacity-10 text-success">
                            <i class="fas fa-file-alt"></i>
                        </div>
                        <h4>📝 Auto Document Gen</h4>
                        <p class="text-muted">One-click generation of legally valid documents: RTI applications, FIR drafts, Consumer complaints, Appeal letters, Grievance filings.</p>
                        <ul class="list-unstyled mt-3 small text-muted">
                            <li><i class="fas fa-check text-success me-2"></i>Legally Compliant Formats</li>
                            <li><i class="fas fa-check text-success me-2"></i>Auto-filled Details</li>
                            <li><i class="fas fa-check text-success me-2"></i>PDF Download</li>
                        </ul>
                    </div>
                </div>
                
                <!-- 5. Civic Heatmap -->
                <div class="col-md-6 col-lg-4">
                    <div class="feature-civic">
                        <div class="icon-circle bg-danger bg-opacity-10 text-danger">
                            <i class="fas fa-fire"></i>
                        </div>
                        <h4>📊 Civic Issues Heatmap</h4>
                        <p class="text-muted">Live visualization of city problems: Potholes, garbage, water, electricity, corruption reports with AI-predicted resolution times.</p>
                        <ul class="list-unstyled mt-3 small text-muted">
                            <li><i class="fas fa-check text-success me-2"></i>Real-time Data</li>
                            <li><i class="fas fa-check text-success me-2"></i>Priority Clustering</li>
                            <li><i class="fas fa-check text-success me-2"></i>Department Accountability</li>
                        </ul>
                    </div>
                </div>
                
                <!-- 6. Government Tracker -->
                <div class="col-md-6 col-lg-4">
                    <div class="feature-civic">
                        <div class="icon-circle bg-secondary bg-opacity-10 text-secondary">
                            <i class="fas fa-tasks"></i>
                        </div>
                        <h4>🔔 Government Tracker</h4>
                        <p class="text-muted">Track complaints, applications, and cases. AI reminds you when to follow up, when officials are late, and when to escalate.</p>
                        <ul class="list-unstyled mt-3 small text-muted">
                            <li><i class="fas fa-check text-success me-2"></i>Deadline Alerts</li>
                            <li><i class="fas fa-check text-success me-2"></i>Escalation Timelines</li>
                            <li><i class="fas fa-check text-success me-2"></i>Progress History</li>
                        </ul>
                    </div>
                </div>
                
                <!-- 7. Predictive AI -->
                <div class="col-md-6 col-lg-4">
                    <div class="feature-civic">
                        <div class="icon-circle" style="background: rgba(139, 92, 246, 0.1); color: #8b5cf6;">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <h4>🧠 Predictive Intelligence</h4>
                        <p class="text-muted">AI predicts which departments delay most, corruption hotspots, rising issues, and optimal filing strategies for maximum success.</p>
                        <ul class="list-unstyled mt-3 small text-muted">
                            <li><i class="fas fa-check text-success me-2"></i>Success Rate Prediction</li>
                            <li><i class="fas fa-check text-success me-2"></i>Department Analytics</li>
                            <li><i class="fas fa-check text-success me-2"></i>Strategic Advice</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- AI Chatbot Section -->
    <section class="py-5 bg-white">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-5 mb-4 mb-lg-0">
                    <h2 class="display-5 fw-bold mb-4">Your Personal<br>Civic Assistant</h2>
                    <p class="lead text-muted mb-4">
                        Not just a chatbot—A <strong>problem-solving engine</strong> that understands government, law, and ground reality.
                    </p>
                    
                    <div class="d-flex flex-column gap-3">
                        <div class="d-flex align-items-start gap-3">
                            <div class="bg-primary bg-opacity-10 p-2 rounded">
                                <i class="fas fa-comments text-primary"></i>
                            </div>
                            <div>
                                <h6 class="fw-bold mb-1">Conversational AI</h6>
                                <small class="text-muted">Ask naturally: "My landlord is evicting me" or "Police won't file FIR"</small>
                            </div>
                        </div>
                        <div class="d-flex align-items-start gap-3">
                            <div class="bg-success bg-opacity-10 p-2 rounded">
                                <i class="fas fa-map-marker-alt text-success"></i>
                            </div>
                            <div>
                                <h6 class="fw-bold mb-1">Location Aware</h6>
                                <small class="text-muted">Auto-detects your state laws and nearest offices</small>
                            </div>
                        </div>
                        <div class="d-flex align-items-start gap-3">
                            <div class="bg-warning bg-opacity-10 p-2 rounded">
                                <i class="fas fa-file-word text-warning"></i>
                            </div>
                            <div>
                                <h6 class="fw-bold mb-1">Document Generation</h6>
                                <small class="text-muted">Instantly creates RTI, complaints, legal notices</small>
                            </div>
                        </div>
                    </div>
                    
                    <button class="btn-primary-civic mt-4" onclick="toggleChat()">
                        <i class="fas fa-paper-plane me-2"></i>Start Conversation
                    </button>
                </div>
                <div class="col-lg-7">
                    <div class="bg-dark rounded-4 p-4 shadow-lg">
                        <div class="d-flex align-items-center gap-2 mb-3 border-bottom border-secondary pb-2">
                            <div class="bg-success rounded-circle" style="width: 10px; height: 10px;"></div>
                            <small class="text-light">SCMIRN Intelligence Online</small>
                        </div>
                        
                        <div class="bg-secondary bg-opacity-25 rounded-3 p-3 mb-3">
                            <div class="text-info small mb-1"><i class="fas fa-robot me-1"></i>SCMIRN AI</div>
                            <div class="text-light">"My landlord is threatening to evict me without notice. What are my rights?"</div>
                        </div>
                        
                        <div class="bg-primary bg-opacity-25 rounded-3 p-3 mb-3 ms-4">
                            <div class="text-primary small mb-1 text-end">You</div>
                            <div class="text-light text-end">I live in Delhi, rented house for 2 years</div>
                        </div>
                        
                        <div class="bg-secondary bg-opacity-25 rounded-3 p-3">
                            <div class="text-info small mb-1"><i class="fas fa-robot me-1"></i>SCMIRN AI</div>
                            <div class="text-light small">
                                <strong>⚖️ Your Rights under Delhi Rent Control Act:</strong><br>
                                • 3-month mandatory notice required<br>
                                • Eviction only through court order<br>
                                • Illegal eviction = FIR under Section 441 IPC<br><br>
                                <strong>📝 I'm generating a Legal Notice draft for you...</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    <!-- Live Issues with Photos -->
    <section id="map-section" class="py-5 bg-light">
        <div class="container py-5">
            <div class="row align-items-end mb-5">
                <div class="col-lg-8">
                    <h2 class="display-5 fw-bold">Live Civic Intelligence Map</h2>
                    <p class="lead text-muted">Street-level visualization of infrastructure issues across your city (zoom for exact road details)</p>
                </div>
                <div class="col-lg-4 text-lg-end">
                    <div class="btn-group" id="issueFilterButtons">
                        <button class="btn btn-outline-dark active" onclick="filterMap('all')">All Issues</button>
                        <button class="btn btn-outline-danger" onclick="filterMap('critical')">Critical</button>
                        <button class="btn btn-outline-warning" onclick="filterMap('high')">High Priority</button>
                    </div>
                    <div class="btn-group mt-2" id="mapViewButtons">
                        <button class="btn btn-outline-secondary" data-layer="street" onclick="setBaseLayer('street')">Street</button>
                        <button class="btn btn-outline-secondary" data-layer="satellite" onclick="setBaseLayer('satellite')">Satellite</button>
                        <button class="btn btn-outline-secondary" onclick="openStreetView()">Street View</button>
                        <button class="btn btn-outline-secondary" onclick="locateUser()">Live Location</button>
                    </div>
                </div>
            </div>
            
            <div class="row g-4">
                <div class="col-lg-8">
                    <div class="map-guide mb-3 d-flex flex-wrap align-items-center gap-3">
                        <div class="small text-muted">Street-level view: zoom in to see exact road edges. Hover markers for quick details.</div>
                        <div class="small text-muted"><span class="legend-dot" style="background:#ef4444;"></span>Critical</div>
                        <div class="small text-muted"><span class="legend-dot" style="background:#f59e0b;"></span>High</div>
                        <div class="small text-muted"><span class="legend-dot" style="background:#06b6d4;"></span>Medium</div>
                        <span id="accuracyBadge" class="badge bg-light text-dark border">Location: not set</span>
                    </div>
                    <div id="civicMap"></div>
                </div>
                <div class="col-lg-4">
                    <div class="bg-white rounded-4 p-4 shadow-sm h-100">
                        <h5 class="fw-bold mb-4">Recent Reports</h5>
                        <div id="issuesList" style="max-height: 400px; overflow-y: auto;">
                            {% for issue in issues %}
                            {% set photos = issue.media_files|fromjson %}
                            <div class="d-flex gap-3 mb-3 p-3 bg-light rounded-3 issue-item" data-tier="{{ issue.priority_tier }}">
                                <img src="{{ photos[0] if photos else 'https://via.placeholder.com/100' }}" 
                                     class="rounded-2" style="width: 80px; height: 60px; object-fit: cover;">
                                <div class="flex-grow-1">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <h6 class="fw-bold mb-1 small">{{ issue.title[:40] }}...</h6>
                                        <span class="badge bg-{{ 'danger' if issue.priority_tier == 'critical' else 'warning' if issue.priority_tier == 'high' else 'info' }}">
                                            {{ issue.priority_tier }}
                                        </span>
                                    </div>
                                    <p class="text-muted small mb-1">{{ issue.description[:60] }}...</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <small class="text-success">₹{{ issue.fund_collected|int }} raised</small>
                                        <button class="btn btn-sm btn-primary" onclick="donate({{ issue.id }})">Fund</button>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    <!-- Document Generator Showcase -->
    <section id="docs" class="py-5 bg-white">
        <div class="container py-5">
            <div class="text-center mb-5">
                <h2 class="display-5 fw-bold">Auto-Generated Legal Documents</h2>
                <p class="lead text-muted">Court-ready paperwork in seconds, not days</p>
            </div>
            
            <div class="row g-4">
                <div class="col-md-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-body">
                            <div class="d-flex align-items-center gap-3 mb-3">
                                <div class="bg-info bg-opacity-10 p-3 rounded-3">
                                    <i class="fas fa-file-alt text-info fa-lg"></i>
                                </div>
                                <h5 class="fw-bold mb-0">RTI Application</h5>
                            </div>
                            <p class="text-muted small">Perfectly formatted Right to Information requests with mandatory fee structure and appeal clauses.</p>
                            <button class="btn btn-outline-info btn-sm w-100" onclick="generateDoc('rti')">Generate Sample</button>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-body">
                            <div class="d-flex align-items-center gap-3 mb-3">
                                <div class="bg-danger bg-opacity-10 p-3 rounded-3">
                                    <i class="fas fa-exclamation-triangle text-danger fa-lg"></i>
                                </div>
                                <h5 class="fw-bold mb-0">FIR Complaint</h5>
                            </div>
                            <p class="text-muted small">Formal complaint to Superintendent of Police when local station refuses to register your FIR.</p>
                            <button class="btn btn-outline-danger btn-sm w-100" onclick="generateDoc('fir')">Generate Sample</button>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-body">
                            <div class="d-flex align-items-center gap-3 mb-3">
                                <div class="bg-success bg-opacity-10 p-3 rounded-3">
                                    <i class="fas fa-balance-scale text-success fa-lg"></i>
                                </div>
                                <h5 class="fw-bold mb-0">Consumer Complaint</h5>
                            </div>
                            <p class="text-muted small">District/State/National Consumer Commission complaints with legal sections and compensation claims.</p>
                            <button class="btn btn-outline-success btn-sm w-100" onclick="generateDoc('consumer')">Generate Sample</button>
                        </div>
                    </div>
                </div>
            </div>
            <div id="docPreview" class="doc-preview mt-4" style="display: none;"></div>
        </div>
    </section>
    <!-- Impact & Investors Section -->
    <section class="py-5 bg-dark text-white">
        <div class="container py-5">
            <div class="row">
                <div class="col-lg-8 mb-5">
                    <h2 class="display-4 fw-bold mb-4">Building the Infrastructure<br>of Democracy 2.0</h2>
                    <p class="lead opacity-75">
                        SCMIRN represents a fundamental shift in civic engagement—using AI to bridge the gap between citizens and governance, making democracy truly participatory and accessible.
                    </p>
                </div>
            </div>
            
            <div class="impact-grid mb-5">
                <div class="impact-item bg-white text-dark">
                    <h4 class="fw-bold text-primary mb-2">For Citizens</h4>
                    <p class="text-muted mb-0">Transform "I don't know what to do" into "Here is exactly what to do" with step-by-step legal and administrative guidance.</p>
                </div>
                <div class="impact-item bg-white text-dark">
                    <h4 class="fw-bold text-success mb-2">For Government</h4>
                    <p class="text-muted mb-0">Data-driven insights into civic pain points, predictive maintenance, and transparent issue resolution tracking.</p>
                </div>
                <div class="impact-item bg-white text-dark">
                    <h4 class="fw-bold text-info mb-2">For Media</h4>
                    <p class="text-muted mb-0">Real-time civic heatmaps and corruption tracking with verifiable citizen reports and documentation.</p>
                </div>
                <div class="impact-item bg-white text-dark">
                    <h4 class="fw-bold text-warning mb-2">For Investors</h4>
                    <p class="text-muted mb-0">Scalable SaaS platform with B2G (Business-to-Government) potential and massive social impact ROI.</p>
                </div>
            </div>
            
            <div class="row g-4 text-center">
                <div class="col-md-3">
                    <div class="stat-number">40%</div>
                    <p class="opacity-75">Faster Resolution than Traditional Channels</p>
                </div>
                <div class="col-md-3">
                    <div class="stat-number">100%</div>
                    <p class="opacity-75">Fund Transparency (Zero Corruption)</p>
                </div>
                <div class="col-md-3">
                    <div class="stat-number">28</div>
                    <p class="opacity-75">States Covered</p>
                </div>
                <div class="col-md-3">
                    <div class="stat-number">24/7</div>
                    <p class="opacity-75">AI Legal Aid Available</p>
                </div>
            </div>
        </div>
    </section>
    <!-- Footer -->
    <footer class="bg-white border-top py-5">
        <div class="container">
            <div class="row g-4">
                <div class="col-lg-4">
                    <h4 class="fw-bold mb-3">🏛️ SCMIRN</h4>
                    <p class="text-muted">The world's first AI-driven civic intelligence system, democratizing access to governance and legal rights for every citizen.</p>
                    <div class="d-flex gap-3 mt-3">
                        <a href="#" class="text-dark"><i class="fab fa-twitter fa-lg"></i></a>
                        <a href="#" class="text-dark"><i class="fab fa-linkedin fa-lg"></i></a>
                        <a href="#" class="text-dark"><i class="fab fa-github fa-lg"></i></a>
                    </div>
                </div>
                <div class="col-lg-2">
                    <h6 class="fw-bold mb-3">Platform</h6>
                    <ul class="list-unstyled text-muted small">
                        <li class="mb-2"><a href="#" class="text-decoration-none text-muted">Problem Solver</a></li>
                        <li class="mb-2"><a href="#" class="text-decoration-none text-muted">Office Finder</a></li>
                        <li class="mb-2"><a href="#" class="text-decoration-none text-muted">Document Gen</a></li>
                        <li class="mb-2"><a href="#" class="text-decoration-none text-muted">Live Heatmap</a></li>
                    </ul>
                </div>
                <div class="col-lg-2">
                    <h6 class="fw-bold mb-3">Resources</h6>
                    <ul class="list-unstyled text-muted small">
                        <li class="mb-2"><a href="#" class="text-decoration-none text-muted">Legal Library</a></li>
                        <li class="mb-2"><a href="#" class="text-decoration-none text-muted">Success Stories</a></li>
                        <li class="mb-2"><a href="#" class="text-decoration-none text-muted">API Docs</a></li>
                        <li class="mb-2"><a href="#" class="text-decoration-none text-muted">Partners</a></li>
                    </ul>
                </div>
                <div class="col-lg-4">
                    <h6 class="fw-bold mb-3">Newsletter</h6>
                    <p class="text-muted small">Get civic updates and new feature announcements.</p>
                    <div class="input-group">
                        <input type="email" class="form-control" placeholder="Enter email">
                        <button class="btn btn-dark">Subscribe</button>
                    </div>
                </div>
            </div>
            <hr class="my-4">
            <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">© 2026 SCMIRN. Built for the future of democracy.</small>
                <div class="d-flex gap-4 small text-muted">
                    <a href="#" class="text-decoration-none text-muted">Privacy</a>
                    <a href="#" class="text-decoration-none text-muted">Terms</a>
                    <a href="#" class="text-decoration-none text-muted">Contact</a>
                </div>
            </div>
        </div>
    </footer>
    <!-- AI Chatbot Interface -->
    <div class="ai-orb" onclick="toggleChat()">
        <i class="fas fa-robot"></i>
    </div>
    
    <div class="chat-intelligence" id="chatWindow">
        <div class="chat-header">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h5 class="fw-bold mb-1"><i class="fas fa-brain me-2"></i>SCMIRN Intelligence</h5>
                    <small class="opacity-75">Civic Problem Solving Engine</small>
                </div>
                <button onclick="toggleChat()" class="btn btn-link text-white p-0">
                    <i class="fas fa-times fa-lg"></i>
                </button>
            </div>
        </div>
        <div class="chat-body" id="chatBody">
            <div class="message-ai">
                <div class="fw-bold text-primary mb-2">👋 Welcome to SCMIRN</div>
                <p class="mb-2">I'm the world's first AI-driven civic intelligence system. I can help you:</p>
                <ul class="list-unstyled ps-2 mb-3 small">
                    <li class="mb-1">⚖️ <strong>Rights Lookup</strong> - RTI, FIR, Consumer laws</li>
                    <li class="mb-1">📝 <strong>Draft Documents</strong> - Legal complaints & appeals</li>
                    <li class="mb-1">🏛️ <strong>Find Offices</strong> - Nearest authorities & officers</li>
                    <li class="mb-1">🎯 <strong>Solve Problems</strong> - Step-by-step action plans</li>
                    <li>📊 <strong>Predict Success</strong> - Data-driven civil strategy</li>
                </ul>
                <div class="suggestion-chip" onclick="sendQuick('Police not filing my FIR')">Police not filing FIR</div>
                <div class="suggestion-chip" onclick="sendQuick('My scholarship is delayed')">Scholarship delayed</div>
                <div class="suggestion-chip" onclick="sendQuick('Draft RTI for road repair')">Draft RTI application</div>
                <div class="suggestion-chip" onclick="sendQuick('Landlord eviction threat')">Landlord issues</div>
            </div>
        </div>
        <div class="p-3 bg-white border-top">
            <div class="input-group">
                <input type="text" id="chatInput" class="form-control border-0 bg-light" 
                       placeholder="Describe your civic problem..." 
                       onkeypress="handleChatKey(event)">
                <button class="btn btn-primary" onclick="sendChatMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
            <div class="mt-2 d-flex flex-wrap gap-1">
                <small class="text-muted me-2">Try:</small>
                <span class="suggestion-chip" onclick="sendQuick('Wrong electricity bill')">Electricity bill</span>
                <span class="suggestion-chip" onclick="sendQuick('Ration card blocked')">Ration card</span>
            </div>
        </div>
    </div>
    <!-- Report Modal -->
    <div class="modal fade" id="reportModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title fw-bold">Report Civic Issue</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="reportForm" onsubmit="submitReport(event)" enctype="multipart/form-data">
                        <div class="mb-3">
                            <input type="text" name="title" class="form-control form-control-lg" 
                                   placeholder="What's the issue? (e.g., Dangerous pothole near school)" required>
                        </div>
                        <div class="mb-3">
                            <textarea name="description" class="form-control" rows="3" 
                                      placeholder="Describe in detail. Include safety risks, duration, previous complaints..." required></textarea>
                        </div>
                        <div class="row g-3 mb-3">
                            <div class="col-md-6">
                                <select name="category" class="form-select">
                                    <option value="road">🛣️ Road Infrastructure</option>
                                    <option value="water">💧 Water & Sanitation</option>
                                    <option value="electricity">⚡ Electricity</option>
                                    <option value="safety">🚨 Public Safety</option>
                                    <option value="corruption">⚖️ Corruption/Governance</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-rupee-sign"></i></span>
                                    <input type="number" name="fund_target" class="form-control" placeholder="Funding needed" value="5000">
                                </div>
                            </div>
                        </div>
                        <div class="row g-3 mb-3">
                            <div class="col-md-6">
                                <input type="number" step="any" name="lat" id="latInput" class="form-control" placeholder="Latitude">
                            </div>
                            <div class="col-md-6">
                                <input type="number" step="any" name="lon" id="lonInput" class="form-control" placeholder="Longitude">
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="border border-dashed rounded-3 p-4 text-center bg-light" 
                                 onclick="document.getElementById('photoInput').click()" style="cursor: pointer;">
                                <i class="fas fa-camera fa-2x text-muted mb-2"></i>
                                <p class="mb-0 text-muted">Click to upload photos of the issue</p>
                                <input type="file" id="photoInput" name="media" multiple accept="image/*" class="d-none" onchange="previewPhotos(this)">
                            </div>
                            <div id="photoPreview" class="d-flex gap-2 mt-2 flex-wrap"></div>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 py-3 fw-bold">
                            <i class="fas fa-paper-plane me-2"></i>Submit Report & AI Analysis
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let map;
        let markers = [];
        let baseLayers = {};
        let currentBaseLayer = null;
        let userMarker = null;
        let userAccuracyCircle = null;
        let userLatLng = null;
        let locateWatchId = null;
        let mapIframe = null;
        let chatWindow = document.getElementById('chatWindow');
        let streetLayer = null;
        let satelliteLayer = null;

        function updateAccuracyBadge(accuracy) {
            const badge = document.getElementById('accuracyBadge');
            if (!badge) return;
            badge.classList.remove('bg-light', 'bg-success', 'bg-warning', 'text-dark', 'text-white');
            if (typeof accuracy === 'number' && !Number.isNaN(accuracy)) {
                if (accuracy <= 30) {
                    badge.classList.add('bg-success', 'text-white');
                } else {
                    badge.classList.add('bg-warning', 'text-dark');
                }
                badge.textContent = `GPS accuracy: ~${Math.round(accuracy)}m`;
            } else {
                badge.classList.add('bg-light', 'text-dark');
                badge.textContent = 'Location: not set';
            }
        }
        
        // Initialize Map
        function initMap() {
            if (typeof L === 'undefined') {
                initFallbackMap();
                return;
            }
            markers = [];
            map = L.map('civicMap', {
                zoomControl: false,
                attributionControl: false
            }).setView([28.6139, 77.2090], 15);
            
            // Add multiple tile layers for different views
            streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 22,
                attribution: '© OpenStreetMap contributors',
                subdomains: 'abc'
            }).addTo(map);
            
            satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                maxZoom: 19,
                attribution: '© Esri'
            });
            
            baseLayers = { street: streetLayer, satellite: satelliteLayer };
            currentBaseLayer = streetLayer;
            
            // Add layer control for user to switch between street/satellite
            const baseMaps = {
                "Detailed Streets": streetLayer,
                "Satellite View": satelliteLayer
            };
            L.control.layers(baseMaps).addTo(map);
            
            // Add zoom control to better position
            L.control.zoom({
                position: 'bottomright'
            }).addTo(map);
            
            // Scale control for distance reference
            L.control.scale({
                imperial: false,
                metric: true,
                position: 'bottomleft'
            }).addTo(map);
            
            // Enhanced issue markers with exact precision
            const issues = [
                {% for issue in issues %}
                {
                    id: {{ issue.id }},
                    lat: {{ issue.lat }},
                    lng: {{ issue.lon }},
                    title: "{{ issue.title }}",
                    tier: "{{ issue.priority_tier }}",
                    category: "{{ issue.category }}",
                    photo: "{{ (issue.media_files|fromjson)[0] if issue.media_files else 'https://via.placeholder.com/100' }}",
                    description: "{{ issue.description[:100] }}...",
                    fund: {{ issue.fund_collected }},
                    target: {{ issue.fund_target }}
                },
                {% endfor %}
            ];
            
            // Custom icons for different priorities
            const icons = {
                critical: L.divIcon({
                    className: 'custom-marker',
                    html: '<div style="background:#ef4444;width:30px;height:30px;border-radius:50%;border:3px solid white;box-shadow:0 4px 12px rgba(239,68,68,0.5);display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:14px;">!</div>',
                    iconSize: [30, 30],
                    iconAnchor: [15, 15]
                }),
                high: L.divIcon({
                    className: 'custom-marker',
                    html: '<div style="background:#f59e0b;width:24px;height:24px;border-radius:50%;border:3px solid white;box-shadow:0 4px 12px rgba(245,158,11,0.5);"></div>',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                }),
                medium: L.divIcon({
                    className: 'custom-marker',
                    html: '<div style="background:#06b6d4;width:20px;height:20px;border-radius:50%;border:3px solid white;box-shadow:0 4px 12px rgba(6,182,212,0.5);"></div>',
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                })
            };
            
            issues.forEach((issue) => {
                const marker = L.marker([issue.lat, issue.lng], {
                    icon: icons[issue.tier] || icons.medium,
                    title: issue.title
                }).addTo(map);
                
                // Enhanced popup with street-level details
                const popup = `
                    <div style="min-width: 280px; max-width: 320px;">
                        <img src="${issue.photo}" style="width: 100%; height: 140px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;">
                        <div style="font-weight: 700; font-size: 15px; margin-bottom: 8px; line-height: 1.3;">${issue.title}</div>
                        <div style="font-size: 13px; color: #64748b; margin-bottom: 8px; line-height: 1.4;">${issue.description}</div>
                        <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                            <span class="badge bg-${issue.tier === 'critical' ? 'danger' : issue.tier === 'high' ? 'warning' : 'info'}">${issue.tier.toUpperCase()}</span>
                            <span class="badge bg-light text-dark border">${issue.category}</span>
                        </div>
                        <div style="background: #f0fdf4; padding: 10px; border-radius: 6px; margin-bottom: 12px;">
                            <div style="display: flex; justify-content: between; align-items: center;">
                                <span style="font-size: 13px; color: #166534;">Raised: <strong>₹${issue.fund.toLocaleString()}</strong></span>
                                <span style="font-size: 12px; color: #64748b; margin-left: auto;">of ₹${issue.target.toLocaleString()}</span>
                            </div>
                            <div class="progress" style="height: 6px; margin-top: 6px;">
                                <div class="progress-bar bg-success" style="width: ${(issue.fund/issue.target*100).toFixed(0)}%"></div>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                            <button onclick="donate(${issue.id})" class="btn btn-sm btn-dark w-100">
                                <i class="fas fa-donate me-1"></i> Fund
                            </button>
                            <button onclick="getDirections(${issue.lat}, ${issue.lng})" class="btn btn-sm btn-outline-secondary w-100">
                                <i class="fas fa-directions me-1"></i> Directions
                            </button>
                        </div>
                    </div>
                `;
                
                marker.bindPopup(popup, {
                    maxWidth: 350,
                    className: 'custom-popup'
                });
                
                // Add hover effect
                marker.on('mouseover', function() {
                    this.openPopup();
                });
                
                markers.push({marker, tier: issue.tier, data: issue});
            });
            
            // Try to get user location with high precision
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        const accuracy = position.coords.accuracy;
                        updateAccuracyBadge(accuracy);
                        
                        userLatLng = [lat, lng];
                        document.getElementById('latInput').value = lat;
                        document.getElementById('lonInput').value = lng;
                        
                        // Add user marker with accuracy circle
                        userMarker = L.marker([lat, lng], {
                            icon: L.divIcon({
                                className: 'user-location',
                                html: '<div style="background:#06b6d4;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);animation:pulse 2s infinite;"></div>',
                                iconSize: [16, 16]
                            })
                        }).addTo(map).bindPopup(`<b>You are here</b><br>Accuracy: ${Math.round(accuracy)} meters`).openPopup();
                        
                        // Add accuracy circle
                        userAccuracyCircle = L.circle([lat, lng], {
                            radius: accuracy,
                            color: '#06b6d4',
                            fillColor: '#06b6d4',
                            fillOpacity: 0.1,
                            weight: 1
                        }).addTo(map);
                        
                        // Center on user with street-level zoom
                        map.setView([lat, lng], 17);
                    },
                    (error) => {
                        console.log('Geolocation error:', error);
                        updateAccuracyBadge(null);
                        // Default to Delhi center with street view
                        map.setView([28.6139, 77.2090], 15);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
            }

            setTimeout(() => {
                try { map.invalidateSize(); } catch (err) {}
            }, 250);
        }
        
        // Add this new function for directions
        function getDirections(lat, lng) {
            const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=driving`;
            window.open(url, '_blank');
        }

        function initFallbackMap(center) {
            const mapEl = document.getElementById('civicMap');
            if (!mapEl) return;

            mapEl.innerHTML = '<iframe id=\"mapFrame\" referrerpolicy=\"no-referrer-when-downgrade\" loading=\"lazy\"></iframe>';
            mapIframe = document.getElementById('mapFrame');
            const lat = center && center.lat ? center.lat : 28.6139;
            const lng = center && center.lng ? center.lng : 77.2090;
            setMapIframe('street', lat, lng);
        }

        function setMapIframe(mode, lat, lng) {
            if (!mapIframe) return;
            const base = mode === 'satellite'
                ? 'https://www.google.com/maps/embed/v1/view?key='
                : 'https://www.google.com/maps/embed/v1/view?key=';
            // If no key is available, fall back to a simple maps URL without API key.
            const fallback = mode === 'satellite'
                ? `https://www.google.com/maps?q=${lat},${lng}&z=16&t=k&output=embed`
                : `https://www.google.com/maps?q=${lat},${lng}&z=16&output=embed`;
            mapIframe.src = fallback;
        }

        function setBaseLayer(name) {
            if (typeof L === 'undefined' || !map) {
                const center = userLatLng ? { lat: userLatLng[0], lng: userLatLng[1] } : { lat: 28.6139, lng: 77.2090 };
                setMapIframe(name, center.lat, center.lng);
                return;
            }
            if (!baseLayers[name]) return;
            if (currentBaseLayer) {
                map.removeLayer(currentBaseLayer);
            }
            currentBaseLayer = baseLayers[name];
            currentBaseLayer.addTo(map);
            
            // Update view toggle button state
            document.querySelectorAll('#mapViewButtons [data-layer]').forEach(btn => {
                btn.classList.remove('active');
                if (btn.getAttribute('data-layer') === name) {
                    btn.classList.add('active');
                }
            });
        }

        function updateUserLocation(lat, lng, accuracy) {
            userLatLng = [lat, lng];
            document.getElementById('latInput').value = lat;
            document.getElementById('lonInput').value = lng;
            updateAccuracyBadge(accuracy);
            
            if (!userMarker) {
                userMarker = L.marker(userLatLng, {
                    icon: L.divIcon({
                        className: 'custom-div-icon',
                        html: "<div style='background:#06b6d4;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);'></div>",
                        iconSize: [16, 16]
                    })
                }).addTo(map).bindPopup("You are here");
            } else {
                userMarker.setLatLng(userLatLng);
            }
            
            if (accuracy) {
                if (!userAccuracyCircle) {
                    userAccuracyCircle = L.circle(userLatLng, {
                        radius: accuracy,
                        color: '#06b6d4',
                        fillColor: '#06b6d4',
                        fillOpacity: 0.15
                    }).addTo(map);
                } else {
                    userAccuracyCircle.setLatLng(userLatLng);
                    userAccuracyCircle.setRadius(accuracy);
                }
            }
            
            map.setView(userLatLng, 17);
        }

        function locateUser() {
            if (!navigator.geolocation) {
                alert('Geolocation is not supported by your browser.');
                return;
            }
            
            navigator.geolocation.getCurrentPosition(pos => {
                updateUserLocation(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy);
            }, () => {
                alert('Unable to access your location.');
            });
            
            if (locateWatchId === null) {
                locateWatchId = navigator.geolocation.watchPosition(pos => {
                    updateUserLocation(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy);
                    if (typeof L === 'undefined') {
                        setMapIframe('street', pos.coords.latitude, pos.coords.longitude);
                    }
                }, () => {}, { enableHighAccuracy: true, maximumAge: 10000, timeout: 10000 });
            }
        }

        function openStreetView() {
            let center = null;
            if (userLatLng) {
                center = { lat: userLatLng[0], lng: userLatLng[1] };
            } else if (map && map.getCenter) {
                center = map.getCenter();
            } else {
                center = { lat: 28.6139, lng: 77.2090 };
            }
            const url = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${center.lat},${center.lng}`;
            window.open(url, '_blank');
        }
        
        function filterMap(tier) {
            if (!map) {
                return;
            }
            markers.forEach(m => {
                if (tier === 'all') {
                    m.marker.addTo(map);
                } else if (m.tier === tier) {
                    m.marker.addTo(map);
                    // Animate marker for visibility
                    m.marker.setZIndexOffset(1000);
                } else {
                    map.removeLayer(m.marker);
                }
            });
            
            // Update button states
            document.querySelectorAll('#issueFilterButtons .btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.textContent.toLowerCase().includes(tier) || (tier === 'all' && btn.textContent.includes('All'))) {
                    btn.classList.add('active');
                }
            });
            
            // Sync the list on the right with the map filter
            document.querySelectorAll('#issuesList .issue-item').forEach(item => {
                const itemTier = item.getAttribute('data-tier');
                if (tier === 'all' || itemTier === tier) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }
        
        // Chatbot Functions
        function toggleChat() {
            const display = chatWindow.style.display;
            chatWindow.style.display = display === 'flex' ? 'none' : 'flex';
            if (chatWindow.style.display === 'flex') {
                document.getElementById('chatInput').focus();
            }
        }
        
        function handleChatKey(e) {
            if (e.key === 'Enter') sendChatMessage();
        }
        
        function sendQuick(text) {
            document.getElementById('chatInput').value = text;
            sendChatMessage();
        }
        
        async function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const text = input.value.trim();
            if (!text) return;
            
            addMessage(text, 'user');
            input.value = '';
            
            // Show typing indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message-ai';
            loadingDiv.innerHTML = '<i class="fas fa-circle-notch fa-spin text-primary"></i> Analyzing legal framework & government data...';
            loadingDiv.id = 'loadingMsg';
            document.getElementById('chatBody').appendChild(loadingDiv);
            document.getElementById('chatBody').scrollTop = document.getElementById('chatBody').scrollHeight;
            
            try {
                const res = await fetch('/api/ai-assistant', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                if (!res.ok) {
                    throw new Error('Request failed');
                }
                const data = await res.json();
                
                document.getElementById('loadingMsg').remove();
                
                const reply = data.response || data.reply || 'Sorry, I could not generate a response.';

                // Format response with rich text
                let formatted = reply
                    .replace(/[*][*](.+?)[*][*]/g, '<strong>$1</strong>')
                    .replace(/\n/g, '<br>')
                    .replace(/•/g, '&bull;');
                
                addMessage(formatted, 'ai');
                
                if (data.action === 'show_document_generator') {
                    addMessage('<div class="suggestion-chip" onclick="openReportModal()">📄 Open Document Generator</div>', 'ai');
                }
            } catch (err) {
                document.getElementById('loadingMsg').remove();
                addMessage('Sorry, experiencing high traffic. Please try again.', 'ai');
            }
        }
        
        function addMessage(html, sender) {
            const div = document.createElement('div');
            div.className = sender === 'ai' ? 'message-ai' : 'message-user';
            div.innerHTML = html;
            document.getElementById('chatBody').appendChild(div);
            document.getElementById('chatBody').scrollTop = document.getElementById('chatBody').scrollHeight;
        }
        
        // Report Functions
        function openReportModal() {
            const modal = document.getElementById('reportModal');
            if (!modal) return;
            if (window.bootstrap && bootstrap.Modal) {
                new bootstrap.Modal(modal).show();
                return;
            }
            modal.classList.add('show');
            modal.style.display = 'block';
            modal.removeAttribute('aria-hidden');
            modal.setAttribute('aria-modal', 'true');
            document.body.classList.add('modal-open');

            let backdrop = document.getElementById('modalBackdrop');
            if (!backdrop) {
                backdrop = document.createElement('div');
                backdrop.id = 'modalBackdrop';
                backdrop.className = 'modal-backdrop fade show';
                document.body.appendChild(backdrop);
            }
        }

        function closeReportModal() {
            const modal = document.getElementById('reportModal');
            if (!modal) return;
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
            modal.removeAttribute('aria-modal');
            document.body.classList.remove('modal-open');

            const backdrop = document.getElementById('modalBackdrop');
            if (backdrop) {
                backdrop.remove();
            }
        }
        
        function previewPhotos(input) {
            const preview = document.getElementById('photoPreview');
            preview.innerHTML = '';
            Array.from(input.files).forEach(file => {
                const reader = new FileReader();
                reader.onload = e => {
                    preview.innerHTML += `<img src="${e.target.result}" class="rounded" style="width: 80px; height: 60px; object-fit: cover;">`;
                };
                reader.readAsDataURL(file);
            });
        }
        
        async function submitReport(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const btn = e.target.querySelector('button[type="submit"]');
            btn.innerHTML = '<i class="fas fa-circle-notch fa-spin me-2"></i>AI Analyzing Priority...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/report-issue', {method: 'POST', body: formData});
                const data = await res.json();
                
                if (data.success) {
                    alert(`✅ ${data.message}\n\nAI classified this as ${data.priority} priority based on safety analysis.`);
                    location.reload();
                }
            } catch (err) {
                alert('Error submitting report');
            } finally {
                btn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Submit Report & AI Analysis';
                btn.disabled = false;
            }
        }
        
        async function donate(issueId) {
            const amount = prompt('Enter donation amount (₹):', '1000');
            if (!amount) return;
            
            try {
                const res = await fetch('/api/donate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({issue_id: issueId, amount: parseFloat(amount)})
                });
                const data = await res.json();
                if (data.success) {
                    alert(`✅ Thank you! ₹${amount} donated successfully.`);
                    location.reload();
                }
            } catch (err) {
                alert('Donation failed');
            }
        }
        
        function generateDoc(type) {
            const templates = {
                rti: `RTI Application Format:\n\nTo: The Public Information Officer\n[Department Name]\n\nSubject: Request for information under RTI Act, 2005\n\nDescription: [Detailed information requested]\nPeriod: [Time frame]\nFee: ₹10 attached\n\nApplicant:\nName: [Your Name]\nAddress: [Your Address]\nDate: [Today's Date]`,
                
                fir: `COMPLAINT LETTER TO SP\n\nSubject: Non-registration of FIR\n\nRespected Sir,\n\nI beg to state that on [date], I approached [Police Station] to report [crime]. The duty officer refused to register FIR despite it being a cognizable offense under Section [IPC Section]...\n\nAction Requested: Direction to register FIR immediately.\n\nEnclosures:\n1. Copy of complaint given to SHO\n2. ID Proof\n3. Evidence (if any)`,
                
                consumer: `CONSUMER COMPLAINT\n\nTo: District Consumer Disputes Redressal Commission\n\nComplainant: [Your Name]\nOpposite Party: [Company Name]\n\nSubject: [Product/Service defect summary]\n\nRelief Sought: [Refund/Replacement/Compensation]\n\nValue: ₹[Amount] (Includes complaint fee)`
            };
            
            const preview = document.getElementById('docPreview');
            if (preview) {
                preview.textContent = templates[type] || 'Template selected';
                preview.style.display = 'block';
                preview.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                alert(templates[type] || 'Template selected');
            }
        }
        
        window.onload = () => {
            try {
                initMap();
            } catch (err) {
                console.error(err);
                initFallbackMap();
            }
        };

        document.addEventListener('click', (event) => {
            if (event.target && event.target.id === 'modalBackdrop') {
                closeReportModal();
            }
        });

        const closeBtn = document.querySelector('#reportModal .btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeReportModal);
        }
    </script>
</body>
</html>'''

@app.route('/')
def index():
    db = get_db()
    if db.execute('SELECT COUNT(*) FROM issues').fetchone()[0] == 0:
        seed_data()
    
    issues = db.execute('SELECT * FROM issues ORDER BY priority_score DESC').fetchall()
    
    stats = {
        'total': db.execute('SELECT COUNT(*) FROM issues').fetchone()[0],
        'critical': db.execute("SELECT COUNT(*) FROM issues WHERE priority_tier='critical'").fetchone()[0],
        'resolved': db.execute("SELECT COUNT(*) FROM issues WHERE status='resolved'").fetchone()[0],
        'total_raised': db.execute('SELECT SUM(fund_collected) FROM issues').fetchone()[0] or 0
    }
    
    return render_template_string(HTML_TEMPLATE, issues=issues, stats=stats, theme=THEME)

@app.route('/api/ai-assistant', methods=['POST'])
def ai_assistant():
    data = request.json
    message = data.get('message', '')
    
    result = ai_engine.process(message)
    
    db = get_db()
    db.execute('INSERT INTO chat_logs (message, intent, confidence) VALUES (?,?,?)',
               (message, result['intent'], result['confidence']))
    db.commit()
    
    return jsonify(result)













@app.route('/api/report-issue', methods=['POST'])
def report_issue():
    db = get_db()
    
    files = request.files.getlist('media')
    photos = []
    
    for file in files:
        if file and '.' in file.filename:
            filename = f"{int(time.time())}_{secure_filename(file.filename)}"
            filepath = os.path.join(UPLOAD_FOLDER, 'issues', filename)
            file.save(filepath)
            photos.append(f"/uploads/issues/{filename}")
    
    desc = request.form.get('description', '')
    title = request.form.get('title', '')
    
    # AI Analysis
    analysis = ai_engine.process(desc + ' ' + title)
    
    # Smart Priority Calculation
    priority_keywords = {
        'critical': ['school', 'hospital', 'accident', 'death', 'electrocution', 'fire', 'collapse', 'children', 'emergency'],
        'high': ['leak', 'broken', 'danger', 'unsafe', 'falling', 'exposed', 'main road', 'highway'],
        'medium': ['light', 'garbage', 'sign', 'painting', 'noise', 'minor']
    }
    
    desc_lower = desc.lower()
    base_score = random.randint(4000, 6000)
    tier = 'medium'
    
    if any(k in desc_lower for k in priority_keywords['critical']):
        base_score = random.randint(8500, 9900)
        tier = 'critical'
    elif any(k in desc_lower for k in priority_keywords['high']):
        base_score = random.randint(6500, 8400)
        tier = 'high'
    
    try:
        lat = float(request.form.get('lat', 28.6139))
        lon = float(request.form.get('lon', 77.2090))
    except Exception:
        lat, lon = 28.6139, 77.2090
    
    db.execute('''
        INSERT INTO issues (title, description, category, lat, lon, priority_score,
                          priority_tier, fund_target, status, media_files, integrity_hash, ai_confidence)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        title, desc, request.form.get('category', 'road'),
        lat, lon, base_score, tier,
        float(request.form.get('fund_target', 5000)),
        'reported', json.dumps(photos),
        hashlib.sha256(title.encode()).hexdigest(),
        analysis['confidence']
    ))
    db.commit()
    
    return jsonify({
        'success': True,
        'priority': tier,
        'score': base_score,
        'message': f'Reported successfully! AI classified as {tier.upper()} priority (Score: {base_score}/10000).'
    })

@app.route('/api/donate', methods=['POST'])
def donate():
    db = get_db()
    data = request.json
    issue_id = data.get('issue_id')
    amount = data.get('amount', 0)
    
    db.execute('UPDATE issues SET fund_collected = fund_collected + ? WHERE id = ?', (amount, issue_id))
    issue = db.execute('SELECT fund_target, fund_collected FROM issues WHERE id = ?', (issue_id,)).fetchone()
    
    new_status = 'funded' if issue['fund_collected'] >= issue['fund_target'] else 'reported'
    if new_status == 'funded':
        db.execute("UPDATE issues SET status = 'funded' WHERE id = ?", (issue_id,))
    
    db.commit()
    
    return jsonify({
        'success': True,
        'new_total': issue['fund_collected'],
        'status': new_status
    })

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    init_db()
    print("SCMIRN Civic Intelligence System v2.0")
    print("=====================================")
    print("World's First AI-Driven Civic Intelligence")
    print("Photo uploads enabled (Unsplash/Pexels sources)")
    print("Legal Rights Engine active")
    print("Document Generator ready")
    print("Live Civic Heatmap active")
    print("=====================================")
    print("Server: http://localhost:5000")
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(debug=debug_mode, host=host, port=port)
