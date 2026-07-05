"""
Seed script for generating 300 realistic fictional Indian criminal profiles.
Called during app startup from main.py lifespan.
"""

import random
import math
from datetime import date, datetime, timedelta

from sqlalchemy import select, func

from app.database import async_session
from app.models.criminal_intelligence import (
    CriminalProfile,
    CriminalAlias,
    CriminalAddress,
    CriminalVehicle,
    CriminalPhoneNumber,
    CriminalSocialAccount,
    CriminalCaseHistory,
    CriminalTimeline,
    CriminalFaceEmbedding,
    CriminalFingerprint,
    CriminalDNAProfile,
    CriminalAssociate,
    DangerLevel,
    WantedStatus,
    Gender,
)

# ---------------------------------------------------------------------------
# Data pools
# ---------------------------------------------------------------------------

MALE_FIRST_NAMES = [
    "Ravi", "Suresh", "Mohit", "Anil", "Vikram", "Deepak", "Rajesh", "Manoj",
    "Sanjay", "Pradeep", "Ashok", "Ramesh", "Vishal", "Rohit", "Amit", "Arjun",
    "Karan", "Akhil", "Nitin", "Pankaj", "Rakesh", "Dinesh", "Mukesh", "Jitendra",
    "Naveen", "Bharat", "Sachin", "Gopal", "Vijay", "Ajay", "Sunil", "Rahul",
    "Gaurav", "Manish", "Harish", "Yogesh", "Satish", "Naresh", "Mahesh", "Umesh",
    "Kamal", "Ranjit", "Balwinder", "Gurpreet", "Jaswinder", "Kuldeep", "Surinder",
    "Parveen", "Irfan", "Salman", "Waseem", "Shakeel", "Nasir", "Imran", "Faisal",
    "Tariq", "Zaheer", "Nadeem", "Asif", "Shahid", "Yusuf", "Anwar", "Feroz",
    "Pappu", "Guddu", "Bunty", "Munna", "Bablu", "Tinku", "Pintu", "Chhotu",
]

FEMALE_FIRST_NAMES = [
    "Sunita", "Rekha", "Geeta", "Neelam", "Pooja", "Kavita", "Suman", "Anita",
    "Meena", "Rani", "Savitri", "Lakshmi", "Priya", "Nisha", "Seema", "Renu",
    "Kiran", "Anjali", "Shanti", "Pushpa", "Parveen", "Shabnam", "Rukhsar",
    "Nasreen", "Fatima", "Ayesha", "Zarina", "Mumtaz", "Gulshan", "Deepika",
]

LAST_NAMES = [
    "Kumar", "Singh", "Sharma", "Verma", "Yadav", "Gupta", "Chauhan", "Thakur",
    "Pandey", "Mishra", "Jha", "Dubey", "Tiwari", "Patel", "Shah", "Malik",
    "Khan", "Sheikh", "Ansari", "Qureshi", "Rajput", "Rawat", "Negi", "Bisht",
    "Jat", "Gurjar", "Meena", "Saini", "Kashyap", "Srivastava", "Tripathi",
    "Chaudhary", "Gill", "Sidhu", "Dhillon", "Bajwa", "Sandhu", "Grewal",
    "Rathore", "Solanki", "Parmar", "Gujjar", "Bhati", "Shekhawat", "Tanwar",
]

NICKNAMES_POOL = [
    "Chhota", "Kala", "Munna", "Langda", "Gabbar", "Tiger", "Pappu", "Kallu",
    "Chiku", "Lambu", "Motu", "Patlu", "Dabang", "Don", "Bhai", "Lala",
    "Takla", "Kalu", "Golu", "Sonu", "Monu", "Raju", "Babu", "Dada",
    "Billa", "Ranga", "Sultan", "Badshah", "Sikander", "Chacha", "Mama",
    "Fauladi", "Hathoda", "Chhupa Rustam", "Shaitan", "Bhoot", "Kaalia",
    "Danger", "Shooter", "Bomb", "Blade", "Katta", "AK", "Rocket", "Cobra",
]

GANG_NAMES = [
    "Rajan Gang", "Dawood Network", "Nayak Syndicate", "Vohra Group",
    "Gurjar Gang", "Bishnoi Gang", "Thakur Cartel", "Meerut Mafia",
    "Lucknow Underworld", "Patna Syndicate",
]

GANG_ROLES = ["leader", "lieutenant", "enforcer", "runner", "financier", "hitman", "informer"]

CRIME_CATEGORIES = [
    "robbery", "murder", "extortion", "drug_trafficking", "kidnapping",
    "theft", "fraud", "assault", "arms_dealing", "cybercrime",
    "counterfeiting", "human_trafficking",
]

OCCUPATIONS = [
    "unemployed", "shopkeeper", "driver", "mechanic", "laborer",
    "businessman", "student", "farmer",
]

BUILDS = ["slim", "medium", "heavy", "muscular"]
COMPLEXIONS = ["fair", "wheatish", "dark"]
HAIR_COLORS = ["black", "dark brown", "grey", "white", "dyed"]
EYE_COLORS = ["black", "dark brown", "brown", "light brown"]
EDUCATION_LEVELS = [
    "illiterate", "primary", "middle school", "high school",
    "intermediate", "graduate", "post-graduate",
]
RELIGIONS = ["Hindu", "Muslim", "Sikh", "Christian", "Buddhist", "Jain"]

CITIES_DATA = [
    ("Delhi", "Delhi", "110"),
    ("Mumbai", "Maharashtra", "400"),
    ("Lucknow", "Uttar Pradesh", "226"),
    ("Patna", "Bihar", "800"),
    ("Jaipur", "Rajasthan", "302"),
    ("Bhopal", "Madhya Pradesh", "462"),
    ("Indore", "Madhya Pradesh", "452"),
    ("Pune", "Maharashtra", "411"),
    ("Hyderabad", "Telangana", "500"),
    ("Kolkata", "West Bengal", "700"),
    ("Chennai", "Tamil Nadu", "600"),
    ("Ahmedabad", "Gujarat", "380"),
    ("Chandigarh", "Chandigarh", "160"),
    ("Noida", "Uttar Pradesh", "201"),
    ("Ghaziabad", "Uttar Pradesh", "201"),
    ("Meerut", "Uttar Pradesh", "250"),
    ("Agra", "Uttar Pradesh", "282"),
    ("Varanasi", "Uttar Pradesh", "221"),
    ("Kanpur", "Uttar Pradesh", "208"),
]

LOCALITIES = [
    "Nehru Nagar", "Gandhi Colony", "Shastri Nagar", "Ambedkar Colony",
    "Rajendra Nagar", "Vikas Nagar", "Patel Nagar", "Subhash Nagar",
    "Indira Colony", "Lajpat Nagar", "Sadar Bazaar", "Civil Lines",
    "Old City Area", "Station Road", "Bypass Road", "Industrial Area",
    "Transport Nagar", "Ram Nagar", "Shiv Colony", "Guru Nagar",
    "Mohalla Qazi", "Idgah Colony", "Kareem Nagar", "Hussain Ganj",
    "Chowk Area", "Gomti Nagar", "Aliganj", "Hazratganj", "Aminabad",
]

POLICE_STATIONS = [
    "Kotwali", "Sadar", "Civil Lines", "Cantt", "City",
    "Gomti Nagar", "Hazratganj", "Chowk", "Kaiserbagh", "Aliganj",
    "Andheri", "Bandra", "Juhu", "Dadar", "Worli",
    "Connaught Place", "Karol Bagh", "Saket", "Dwarka", "Rohini",
    "Koramangala", "Whitefield", "Electronic City", "Marathahalli",
]

COURTS = [
    "District Court", "Sessions Court", "High Court",
    "Metropolitan Magistrate Court", "Chief Judicial Magistrate Court",
    "Additional Sessions Court", "Fast Track Court",
]

BNS_SECTIONS = [
    "BNS 103 (Murder)", "BNS 309 (Robbery)", "BNS 308 (Extortion)",
    "BNS 303 (Theft)", "BNS 140 (Kidnapping)", "BNS 74 (Assault)",
    "Arms Act 25/27", "NDPS Act 21/22", "BNS 318 (Cheating)",
    "BNS 351 (Criminal Intimidation)",
]

WEAPONS = [
    "country-made pistol", "revolver", "knife", "sword", "axe",
    "iron rod", "hockey stick", "baseball bat", "acid", "bomb",
    "AK-47", "carbine", "grenade",
]

IDENTIFYING_MARKS = [
    "scar on left cheek", "burn mark on right arm", "tattoo on forearm",
    "mole near left eye", "missing front tooth", "limping gait",
    "scar on forehead", "birthmark on neck", "tattoo on chest",
    "pierced left ear", "broken nose", "scar on right hand",
]

MOTORCYCLE_MAKES = [
    ("Hero", ["Splendor", "HF Deluxe", "Passion", "Glamour", "Xtreme"]),
    ("Bajaj", ["Pulsar 150", "Pulsar 220", "Avenger", "Dominar", "CT100"]),
    ("Royal Enfield", ["Classic 350", "Bullet 350", "Thunderbird", "Himalayan", "Meteor"]),
    ("Honda", ["Shine", "Unicorn", "Hornet", "CB350"]),
    ("TVS", ["Apache", "Jupiter", "Ntorq", "Raider"]),
]

CAR_MAKES = [
    ("Maruti", ["Swift", "Alto", "WagonR", "Dzire", "Baleno", "Brezza", "Ertiga"]),
    ("Hyundai", ["i20", "Creta", "Verna", "Venue", "i10"]),
    ("Tata", ["Nexon", "Punch", "Harrier", "Safari", "Altroz"]),
    ("Mahindra", ["Scorpio", "Bolero", "Thar", "XUV700", "XUV300"]),
]

VEHICLE_COLORS = ["white", "black", "red", "silver", "grey", "blue", "green", "maroon"]

RTO_CODES = [
    "UP-14", "UP-15", "UP-16", "UP-32", "UP-65", "UP-70", "UP-78", "UP-80",
    "DL-01", "DL-02", "DL-03", "DL-04", "DL-05", "DL-08", "DL-09", "DL-10",
    "MH-01", "MH-02", "MH-03", "MH-04", "MH-12", "MH-14",
    "RJ-14", "RJ-19", "RJ-20", "RJ-27",
    "HR-26", "HR-51", "HR-55",
    "BR-01", "BR-06", "BR-19",
    "MP-04", "MP-09",
]

CARRIERS = ["Jio", "Airtel", "Vi", "BSNL"]

SOCIAL_PLATFORMS = [
    ("Facebook", "facebook.com"),
    ("Instagram", "instagram.com"),
    ("WhatsApp", None),
    ("Telegram", "t.me"),
    ("Twitter", "twitter.com"),
]

TIMELINE_EVENT_TYPES = [
    "first_offense", "arrest", "bail", "court_hearing", "conviction",
    "prison_release", "gang_initiation", "weapon_seizure", "encounter",
    "surveillance", "tip_received", "absconding", "surrendered",
]

CASE_STATUSES = ["under_investigation", "chargesheet_filed", "trial", "convicted", "acquitted", "closed"]
VERDICTS = ["guilty", "not_guilty", "pending", None]

CODIS_LOCI = [
    "CSF1PO", "D3S1358", "D5S818", "D7S820", "D8S1179",
    "D13S317", "D16S539", "D18S51", "D21S11", "FGA",
    "TH01", "TPOX", "vWA", "D2S1338", "D19S433",
    "D1S1656", "D2S441", "D10S1248", "D12S391", "D22S1045",
]

LABORATORIES = [
    "CFSL New Delhi", "FSL Lucknow", "FSL Chandigarh",
    "FSL Hyderabad", "FSL Mumbai", "CFSL Kolkata",
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def random_date(start_year: int, end_year: int) -> date:
    """Generate a random date between start_year-01-01 and end_year-12-31."""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_phone_number() -> str:
    """Generate an Indian mobile number."""
    prefix = random.choice(["9", "8", "7"])
    number = "".join([str(random.randint(0, 9)) for _ in range(9)])
    return f"+91 {prefix}{number}"


def generate_registration() -> str:
    """Generate an Indian vehicle registration number."""
    rto = random.choice(RTO_CODES)
    series = random.choice("ABCDEFGHJKLMNPRSTUVWXYZ") + random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")
    number = f"{random.randint(1000, 9999)}"
    return f"{rto}-{series}-{number}"


def generate_fir_number(year: int) -> str:
    """Generate a realistic FIR number."""
    return f"FIR-{year}-{random.randint(1000, 9999)}"


def generate_face_embedding() -> list:
    """Generate a random 512-dimensional normalized float vector (simulates insightface output)."""
    raw = [random.gauss(0, 1) for _ in range(512)]
    magnitude = math.sqrt(sum(x * x for x in raw))
    if magnitude == 0:
        magnitude = 1.0
    return [round(x / magnitude, 6) for x in raw]


def generate_fingerprint_minutiae() -> list:
    """Generate mock minutiae data: list of 20-40 random {x, y, angle, type} points."""
    count = random.randint(20, 40)
    minutiae_types = ["ridge_ending", "bifurcation", "short_ridge", "dot"]
    points = []
    for _ in range(count):
        points.append({
            "x": round(random.uniform(0, 500), 2),
            "y": round(random.uniform(0, 500), 2),
            "angle": round(random.uniform(0, 360), 2),
            "type": random.choice(minutiae_types),
        })
    return points


def generate_dna_loci() -> dict:
    """Generate mock CODIS loci markers."""
    loci = {}
    for locus in CODIS_LOCI:
        allele1 = round(random.uniform(6, 40), 1)
        allele2 = round(random.uniform(6, 40), 1)
        loci[locus] = [allele1, allele2]
    return loci


def weighted_choice(options: list, weights: list):
    """Weighted random choice without numpy."""
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for option, weight in zip(options, weights):
        cumulative += weight
        if r <= cumulative:
            return option
    return options[-1]


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------


async def seed_criminal_profiles():
    """Generate and insert 300 fictional Indian criminal profiles with all associated data."""
    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(func.count()).select_from(CriminalProfile))
        count = result.scalar()
        if count >= 200:
            print(f"[seed_criminals] Skipping: {count} profiles already exist.")
            return

        print("[seed_criminals] Seeding 300 criminal profiles...")
        random.seed(42)

        # Distribution weights
        wanted_statuses = [
            WantedStatus.NOT_WANTED, WantedStatus.WANTED, WantedStatus.MOST_WANTED,
            WantedStatus.SURRENDERED, WantedStatus.ARRESTED, WantedStatus.ABSCONDING,
        ]
        wanted_weights = [60, 15, 10, 5, 5, 5]

        danger_levels = [DangerLevel.LOW, DangerLevel.MEDIUM, DangerLevel.HIGH, DangerLevel.EXTREME]
        danger_weights = [40, 30, 20, 10]

        all_profiles = []
        all_related_objects = []
        gang_members = {}  # gang_name -> list of (profile_index, full_name)

        # Generate 300 profiles
        for i in range(300):
            # Gender: 90% male, 10% female
            is_female = random.random() < 0.10
            gender = Gender.FEMALE if is_female else Gender.MALE

            if is_female:
                first_name = random.choice(FEMALE_FIRST_NAMES)
            else:
                first_name = random.choice(MALE_FIRST_NAMES)

            last_name = random.choice(LAST_NAMES)
            full_name = f"{first_name} {last_name}"
            father_first = random.choice(MALE_FIRST_NAMES)
            father_name = f"{father_first} {last_name}"

            criminal_id = f"CR-{i + 1:04d}"

            # Nicknames (1-3)
            num_nicknames = random.randint(1, 3)
            nicknames = random.sample(NICKNAMES_POOL, min(num_nicknames, len(NICKNAMES_POOL)))

            # Date of birth (1965-2000)
            dob = random_date(1965, 2000)

            # Gang membership (40%)
            gang_name = None
            gang_role = None
            if random.random() < 0.40:
                gang_name = random.choice(GANG_NAMES)
                gang_role = random.choice(GANG_ROLES)

            # Crime categories (1-3)
            num_crimes = random.randint(1, 3)
            crime_cats = random.sample(CRIME_CATEGORIES, num_crimes)

            # Wanted status and danger level
            wanted_status = weighted_choice(wanted_statuses, wanted_weights)
            danger_level = weighted_choice(danger_levels, danger_weights)

            # Physical attributes
            height_cm = round(random.uniform(155, 190), 1)
            weight_kg = round(random.uniform(50, 100), 1)
            build = random.choice(BUILDS)
            complexion = random.choice(COMPLEXIONS)
            hair_color = random.choice(HAIR_COLORS)
            eye_color = random.choice(EYE_COLORS)

            # Identifying marks (0-2)
            num_marks = random.randint(0, 2)
            marks = random.sample(IDENTIFYING_MARKS, num_marks) if num_marks > 0 else []

            # Other fields
            occupation = random.choice(OCCUPATIONS)
            education = random.choice(EDUCATION_LEVELS)
            religion = random.choice(RELIGIONS)
            nationality = "Indian"

            # Weapons (0-3)
            num_weapons = random.randint(0, 3)
            known_weapons = random.sample(WEAPONS, num_weapons) if num_weapons > 0 else []

            # Arrest/conviction stats
            total_arrests = random.randint(0, 12)
            total_convictions = random.randint(0, min(total_arrests, 5))
            total_firs = random.randint(max(1, total_arrests), total_arrests + 8)

            # Dates
            career_start_year = max(dob.year + 16, 1985)
            first_offense = random_date(career_start_year, min(career_start_year + 5, 2023))
            last_activity_year = random.randint(first_offense.year, 2024)
            last_known_activity = datetime(
                last_activity_year,
                random.randint(1, 12),
                random.randint(1, 28),
                random.randint(0, 23),
                random.randint(0, 59),
            )

            # Reward amount for wanted/most_wanted
            reward_amount = None
            if wanted_status in (WantedStatus.WANTED, WantedStatus.MOST_WANTED):
                reward_amount = random.choice([
                    10000, 25000, 50000, 100000, 200000, 500000, 1000000, 2500000, 5000000,
                ])

            # Prison history
            prison_history = None
            if total_convictions > 0:
                prisons = ["Tihar Jail", "Arthur Road Jail", "Yerwada Jail",
                           "Sabarmati Jail", "District Jail", "Central Jail"]
                prison_history = []
                for _ in range(min(total_convictions, 3)):
                    prison_history.append({
                        "prison": random.choice(prisons),
                        "from": str(random_date(first_offense.year, 2022)),
                        "to": str(random_date(2020, 2024)),
                        "sentence_years": random.randint(1, 10),
                    })

            # Bail status
            bail_statuses = ["on_bail", "bail_rejected", "bail_pending", "no_bail_required", None]
            bail_status = random.choice(bail_statuses)

            # City for station_id
            city_data = random.choice(CITIES_DATA)

            # Modus operandi
            modus_templates = [
                f"Operates in {city_data[0]} area. Known for {crime_cats[0]} using {random.choice(WEAPONS) if known_weapons else 'sharp weapons'}.",
                f"Targets isolated victims in {random.choice(LOCALITIES)}. Uses disguise and stolen vehicles.",
                f"Part of organized {crime_cats[0]} ring. Operates across state borders.",
                f"Uses social media to identify targets. Known for meticulous planning.",
                f"Strikes during night hours in residential areas. Quick getaway using motorcycles.",
                f"Operates with 2-3 associates. Uses threats and intimidation.",
            ]
            modus_operandi = random.choice(modus_templates)

            profile = CriminalProfile(
                criminal_id=criminal_id,
                full_name=full_name,
                father_name=father_name,
                nicknames=nicknames,
                date_of_birth=dob,
                gender=gender,
                nationality=nationality,
                religion=religion,
                caste=None,
                occupation=occupation,
                education=education,
                height_cm=height_cm,
                weight_kg=weight_kg,
                build=build,
                complexion=complexion,
                hair_color=hair_color,
                eye_color=eye_color,
                identifying_marks=marks if marks else None,
                gang_name=gang_name,
                gang_role=gang_role,
                crime_categories=crime_cats,
                modus_operandi=modus_operandi,
                known_weapons=known_weapons if known_weapons else None,
                wanted_status=wanted_status,
                danger_level=danger_level,
                reward_amount=reward_amount,
                total_arrests=total_arrests,
                total_convictions=total_convictions,
                total_firs=total_firs,
                first_offense_date=first_offense,
                last_known_activity=last_known_activity,
                prison_history=prison_history,
                court_cases=None,
                bail_status=bail_status,
                notes=None,
                is_active=True,
                added_by=1,
                station_id=f"{city_data[0][:3].upper()}-PS-{random.randint(1, 20):02d}",
            )

            all_profiles.append(profile)

            # Track gang members for associates later
            if gang_name:
                if gang_name not in gang_members:
                    gang_members[gang_name] = []
                gang_members[gang_name].append((i, full_name))

            # --- Related objects ---
            related = []

            # Aliases (1-3)
            num_aliases = random.randint(1, 3)
            alias_names_used = set()
            for _ in range(num_aliases):
                alias_prefix = random.choice(NICKNAMES_POOL)
                alias_suffix = random.choice(LAST_NAMES)
                alias_name = f"{alias_prefix} {alias_suffix}"
                if alias_name in alias_names_used:
                    alias_name = f"{random.choice(MALE_FIRST_NAMES)} {alias_suffix}"
                alias_names_used.add(alias_name)
                related.append(CriminalAlias(
                    criminal_id=None,  # will be set after flush
                    alias_name=alias_name,
                    context=random.choice([
                        "Known in local area", "Used during operations",
                        "Police records", "Underworld name",
                        "Childhood nickname", "Gang identity",
                    ]),
                ))

            # Addresses (1-2)
            num_addresses = random.randint(1, 2)
            for addr_idx in range(num_addresses):
                addr_city = random.choice(CITIES_DATA)
                locality = random.choice(LOCALITIES)
                house_no = f"{random.randint(1, 500)}/{random.choice('ABCDEFGH')}"
                address_line = f"{house_no}, {locality}, {addr_city[0]}"
                pincode = f"{addr_city[2]}{random.randint(100, 999):03d}"
                related.append(CriminalAddress(
                    criminal_id=None,
                    address_type=random.choice(["permanent", "current", "temporary", "hideout"]),
                    address_line=address_line,
                    city=addr_city[0],
                    state=addr_city[1],
                    pincode=pincode,
                    is_current=(addr_idx == 0),
                    verified=random.choice([True, False]),
                ))

            # Vehicles (0-2)
            num_vehicles = random.randint(0, 2)
            for _ in range(num_vehicles):
                if random.random() < 0.6:
                    # Motorcycle
                    make_data = random.choice(MOTORCYCLE_MAKES)
                    v_type = "motorcycle"
                else:
                    # Car
                    make_data = random.choice(CAR_MAKES)
                    v_type = "car"
                related.append(CriminalVehicle(
                    criminal_id=None,
                    vehicle_type=v_type,
                    make=make_data[0],
                    model=random.choice(make_data[1]),
                    color=random.choice(VEHICLE_COLORS),
                    registration_number=generate_registration(),
                    chassis_number=None,
                    is_stolen=random.random() < 0.25,
                    notes=None,
                ))

            # Phone numbers (1-3)
            num_phones = random.randint(1, 3)
            for _ in range(num_phones):
                related.append(CriminalPhoneNumber(
                    criminal_id=None,
                    phone_number=generate_phone_number(),
                    phone_type=random.choice(["mobile", "mobile", "mobile", "landline"]),
                    carrier=random.choice(CARRIERS),
                    is_active=random.choice([True, True, True, False]),
                    registered_name=f"{random.choice(MALE_FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                ))

            # Social accounts (0-2)
            num_social = random.randint(0, 2)
            if num_social > 0:
                platforms = random.sample(SOCIAL_PLATFORMS, num_social)
                for platform_name, domain in platforms:
                    username = f"{first_name.lower()}{random.randint(10, 9999)}"
                    profile_url = f"https://{domain}/{username}" if domain else None
                    related.append(CriminalSocialAccount(
                        criminal_id=None,
                        platform=platform_name,
                        username=username,
                        profile_url=profile_url,
                        is_active=random.choice([True, False]),
                        notes=None,
                    ))

            # Case history (1-5)
            num_cases = random.randint(1, 5)
            for case_idx in range(num_cases):
                offense_year = random.randint(first_offense.year, 2024)
                offense_date = random_date(offense_year, offense_year)
                arrest_date = None
                if random.random() < 0.7:
                    arrest_days_later = random.randint(0, 365)
                    arrest_date = offense_date + timedelta(days=arrest_days_later)

                num_sections = random.randint(1, 3)
                sections = random.sample(BNS_SECTIONS, num_sections)

                ps_city = random.choice(CITIES_DATA)
                ps_name = f"{random.choice(POLICE_STATIONS)} PS"
                court = f"{random.choice(COURTS)}, {ps_city[0]}"

                case_status = random.choice(CASE_STATUSES)
                verdict = None
                sentence = None
                if case_status == "convicted":
                    verdict = "guilty"
                    sentence = f"{random.randint(1, 14)} years RI"
                elif case_status == "acquitted":
                    verdict = "not_guilty"

                related.append(CriminalCaseHistory(
                    criminal_id=None,
                    fir_number=generate_fir_number(offense_year),
                    case_type=random.choice(crime_cats),
                    sections_applied=sections,
                    police_station=ps_name,
                    district=ps_city[0],
                    state=ps_city[1],
                    date_of_offense=offense_date,
                    date_of_arrest=arrest_date,
                    court_name=court,
                    case_status=case_status,
                    verdict=verdict,
                    sentence=sentence,
                    bail_granted=random.choice([True, False]),
                    description=f"Case related to {random.choice(crime_cats)} in {ps_city[0]} area.",
                ))

            # Timeline (3-8 events)
            num_events = random.randint(3, 8)
            timeline_start = first_offense.year
            timeline_end = min(2024, last_activity_year)
            for evt_idx in range(num_events):
                evt_year = random.randint(timeline_start, timeline_end)
                evt_date = random_date(evt_year, evt_year)
                evt_type = random.choice(TIMELINE_EVENT_TYPES)

                evt_titles = {
                    "first_offense": f"First recorded offense in {random.choice(CITIES_DATA)[0]}",
                    "arrest": f"Arrested by {random.choice(POLICE_STATIONS)} PS",
                    "bail": "Released on bail from court",
                    "court_hearing": f"Court hearing at {random.choice(COURTS)}",
                    "conviction": f"Convicted under {random.choice(BNS_SECTIONS)}",
                    "prison_release": "Released from prison after serving sentence",
                    "gang_initiation": f"Joined {gang_name or random.choice(GANG_NAMES)}",
                    "weapon_seizure": f"Weapons seized: {random.choice(WEAPONS)}",
                    "encounter": f"Police encounter in {random.choice(CITIES_DATA)[0]}",
                    "surveillance": "Placed under police surveillance",
                    "tip_received": "Intelligence tip received about location",
                    "absconding": f"Absconded from {random.choice(CITIES_DATA)[0]}",
                    "surrendered": "Surrendered before authorities",
                }
                title = evt_titles.get(evt_type, f"Activity recorded: {evt_type}")

                related.append(CriminalTimeline(
                    criminal_id=None,
                    event_date=evt_date,
                    event_type=evt_type,
                    title=title,
                    description=f"Event recorded during ongoing investigation. Location: {random.choice(CITIES_DATA)[0]}.",
                    location=random.choice(CITIES_DATA)[0],
                    extra_data={"source": random.choice(["intelligence", "fir", "surveillance", "informer"])},
                ))

            # Face embedding (1)
            related.append(CriminalFaceEmbedding(
                criminal_id=None,
                embedding=generate_face_embedding(),
                image_path=f"/data/faces/{criminal_id.lower()}_001.jpg",
                model_name="insightface_buffalo",
                embedding_dim=512,
                quality_score=round(random.uniform(0.6, 0.99), 3),
            ))

            # Fingerprint (1)
            finger_types = [
                "right_thumb", "right_index", "right_middle",
                "left_thumb", "left_index", "left_middle",
            ]
            related.append(CriminalFingerprint(
                criminal_id=None,
                finger_type=random.choice(finger_types),
                template_data=generate_fingerprint_minutiae(),
                image_path=f"/data/fingerprints/{criminal_id.lower()}_fp.wsq",
                quality_score=round(random.uniform(0.5, 0.95), 3),
            ))

            # DNA profile (1)
            dna_id = f"DNA-IN-{random.randint(2018, 2024)}-{random.randint(10000, 99999)}"
            related.append(CriminalDNAProfile(
                criminal_id=None,
                dna_id=dna_id,
                sample_number=f"S-{random.randint(100000, 999999)}",
                laboratory=random.choice(LABORATORIES),
                collection_date=random_date(2018, 2024),
                profile_data={"type": "STR", "kit": "GlobalFiler", "status": "complete"},
                loci_markers=generate_dna_loci(),
            ))

            all_related_objects.append(related)

        # --- Insert in batches of 50 ---
        BATCH_SIZE = 50
        profile_ids = []  # store (index, db_id) after flush

        for batch_start in range(0, 300, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, 300)
            batch_profiles = all_profiles[batch_start:batch_end]

            db.add_all(batch_profiles)
            await db.flush()

            # Now assign IDs to related objects
            for idx in range(batch_start, batch_end):
                profile = all_profiles[idx]
                profile_id = profile.id
                profile_ids.append((idx, profile_id))

                for obj in all_related_objects[idx]:
                    obj.criminal_id = profile_id

                db.add_all(all_related_objects[idx])

            await db.flush()
            print(f"[seed_criminals] Batch {batch_start + 1}-{batch_end} inserted.")

        # --- Create associate links ---
        associate_objects = []

        # Link gang members to each other
        for gang, members in gang_members.items():
            if len(members) < 2:
                continue
            for idx, (member_idx, member_name) in enumerate(members):
                # Each gang member gets 1-3 associates from same gang
                num_assoc = min(random.randint(1, 3), len(members) - 1)
                other_members = [m for j, m in enumerate(members) if j != idx]
                chosen = random.sample(other_members, min(num_assoc, len(other_members)))

                member_profile_id = all_profiles[member_idx].id
                for assoc_idx, assoc_name in chosen:
                    assoc_profile_id = all_profiles[assoc_idx].id
                    associate_objects.append(CriminalAssociate(
                        criminal_id=member_profile_id,
                        associate_criminal_id=assoc_profile_id,
                        associate_name=assoc_name,
                        relationship_type=random.choice([
                            "gang_member", "partner", "accomplice",
                            "supplier", "handler", "subordinate",
                        ]),
                        gang_connection=gang,
                        notes=None,
                    ))

        # Also link some random non-gang criminals (about 30 random links)
        non_gang_indices = [i for i in range(300) if all_profiles[i].gang_name is None]
        if len(non_gang_indices) >= 2:
            for _ in range(30):
                pair = random.sample(non_gang_indices, 2)
                idx_a, idx_b = pair
                associate_objects.append(CriminalAssociate(
                    criminal_id=all_profiles[idx_a].id,
                    associate_criminal_id=all_profiles[idx_b].id,
                    associate_name=all_profiles[idx_b].full_name,
                    relationship_type=random.choice([
                        "acquaintance", "neighbor", "relative",
                        "co-accused", "informer", "business_partner",
                    ]),
                    gang_connection=None,
                    notes=None,
                ))

        # Insert associates in batches
        for batch_start in range(0, len(associate_objects), BATCH_SIZE):
            batch = associate_objects[batch_start:batch_start + BATCH_SIZE]
            db.add_all(batch)
            await db.flush()

        await db.commit()
        print(f"[seed_criminals] Done. Inserted 300 profiles with {len(associate_objects)} associate links.")
