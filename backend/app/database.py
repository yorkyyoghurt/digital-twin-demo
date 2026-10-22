
import hashlib  # Hulpbestand om wachtwoorden veilig te versleutelen (geheim te maken)
import hmac     # Hulpbestand om versleutelde wachtwoorden veilig te vergelijken
import os       # Hulpbestand om te praten met het besturingssysteem van de computer
import sqlite3  # Het programma waarmee we de database-bestanden aanmaken en uitlezen
from contextlib import contextmanager  # Hulpje om de database netjes te openen en te sluiten
from datetime import datetime          # Hulpje om de datum en tijd van nu op te vragen

# hier wordt het pad naar de database opgeslagen, zodat we overal in de code makkelijk bij kunnen
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "peep_trials.db")

# Een lijst met alle namen van de vakjes die we per patiënt willen opslaan
TRIAL_COLUMNS = ["patient_number", "pao2", "fio2", "pao2_fio2", "initial_peep", "peep","tidal_volume", "respiratory_rate", 
                "plateau_pressure", "spo2", "patient_position", "eit_file", "notes",]


@contextmanager # opent database en zorgt dat hij altijd netjes wordt afgesloten
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # makkelijker om kolomnamen te gebruiken bij het uitlezen van rijen
    conn.execute("PRAGMA foreign_keys = ON") # zorgt voor integriteit van database, zodat er geen losse stappen in trial_steps kunnen bestaan zonder een bijbehorende trial en bij het verwijderen van een trial ook de bijbehorende stappen worden verwijderd
    try:
        with conn:                          # commit, of roll back (ongedaan maken van stappen, zorgt ervoor dat alles netjes blijft) als er een error is
            yield conn                      # geeft de verbinding met de database terug aan de code die connect() gebruikt, zorgt dat de with command werkt, en resumes execution after the yield statement
    finally:
        conn.close()                        # sluit de verbinding met de database, zodat er geen losse verbindingen blijven bestaan ook al is er een error (voorkomt werkgeheugen verbruik)


def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (                      -- tabel voor gebruikers
            username TEXT PRIMARY KEY,                           -- gebruikersnaam is uniek en wordt gebruikt om in te loggen
            salt BLOB NOT NULL,                                  -- salt is een random stukje data dat wordt toegevoegd aan het wachtwoord voordat het wordt versleuteld, zodat dezelfde wachtwoorden van verschillende gebruikers niet hetzelfde worden opgeslagen
            password_hash BLOB NOT NULL                      -- het versleutelde wachtwoord, dat wordt vergeleken bij het inloggen
        );
        CREATE TABLE IF NOT EXISTS trials (                     -- tabel voor trials
            id INTEGER PRIMARY KEY AUTOINCREMENT,               -- uniek nummer voor elke trial, wordt automatisch opgehoogd bij elke nieuwe trial
            patient_number TEXT NOT NULL,                       -- uniek nummer voor elke patiënt, wordt gebruikt om de trial te identificeren
            doctor TEXT, -- naam van de arts die de trial heeft uitgevoerd
            created_at TEXT NOT NULL,                           -- datum en tijd van aanmaken van de trial, wordt automatisch ingevuld bij het aanmaken van de trial
            pao2 REAL, fio2 REAL, pao2_fio2 REAL, initial_peep INTEGER,     -- de waarden van de patiënt bij het aanmaken van de trial, worden ingevuld door de arts (Real = decimaal getal, Integer = heel getal)
            peep REAL, tidal_volume REAL, respiratory_rate REAL,
            plateau_pressure REAL, spo2 REAL,
            patient_position TEXT, eit_file TEXT, notes TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_trials_patient ON trials(patient_number);        -- index op patient_number, zodat we snel kunnen zoeken op patient_number
        CREATE TABLE IF NOT EXISTS trial_steps (                -- tabel voor de stappen van een trial
            id INTEGER PRIMARY KEY AUTOINCREMENT,               -- uniek nummer voor elke stap, wordt automatisch opgehoogd bij elke nieuwe stap    
            trial_id INTEGER NOT NULL REFERENCES trials(id) ON DELETE CASCADE,          -- maakt een kolom trial_id die verwijst naar de id van de trial waar de stap bij hoort, en zorgt dat als een trial wordt verwijderd, ook alle bijbehorende stappen worden verwijderd
            step_number INTEGER NOT NULL,
            peep REAL NOT NULL,
            p_plateau REAL NOT NULL,
            eit_file TEXT,
            recorded_at TEXT NOT NULL
        );
        """)

# wachtwoord versleuteling
def _hash(password, salt): # wachtwoord versleutelen met salt, zodat het veilig kan worden opgeslagen in de database
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)

# dokter id aanmaken
def create_user(username, password): # aanmaken van een nieuwe gebruiker, met een random salt en het versleutelde wachtwoord. Als er een bestaande gebruiker is met dezelfde gebruikersnaam, wordt er een IntegrityError gegooid en wordt False teruggegeven. Als de gebruiker succesvol is aangemaakt, wordt True teruggegeven.
    salt = os.urandom(16)
    try:
        with connect() as conn:
            conn.execute("INSERT INTO users VALUES (?, ?, ?)",
                         (username, salt, _hash(password, salt)))
        return True
    except sqlite3.IntegrityError:
        return False

# login check
def check_login(username, password): # zoekt in de database naar de gebruiker met de opgegeven gebruikersnaam, en vergelijkt het versleutelde wachtwoord met het versleutelde wachtwoord in de database. Als de gebruiker niet bestaat of het wachtwoord niet klopt, wordt False teruggegeven. Als het wachtwoord klopt, wordt True teruggegeven.
    with connect() as conn:
        row = conn.execute("SELECT salt, password_hash FROM users WHERE username = ?",
                           (username,)).fetchone()
    if row is None:
        return False
    return hmac.compare_digest(row["password_hash"], _hash(password, row["salt"]))

# tijdstip
def _now(): # geeft de huidige datum en tijd terug in ISO 8601 formaat, zodat we het kunnen opslaan in de database. We gebruiken timespec="seconds" om de milliseconden weg te laten, zodat het makkelijker is om te lezen en te vergelijken.
    return datetime.now().isoformat(timespec="seconds")

# aanmaken en opslaan van een nieuwe PEEP trial in de database
def create_trial(doctor, data): # maakt een nieuwe trial aan in de database, roept de waarden van de patiënt op uit de data dictionary, en voegt de naam van de arts en de datum en tijd van aanmaken toe. Geeft het id van de nieuwe trial terug.
    values = {c: data.get(c) for c in TRIAL_COLUMNS}
    values["doctor"] = doctor
    values["created_at"] = _now()
    cols = ", ".join(TRIAL_COLUMNS)
    marks = ", ".join(":" + c for c in TRIAL_COLUMNS)
    with connect() as conn:
        cur = conn.execute(
            f"INSERT INTO trials (doctor, created_at, {cols}) "
            f"VALUES (:doctor, :created_at, {marks})", values)
        return cur.lastrowid

# registratie van de stappen van een trial in de database
def add_step(trial_id, step_number, peep, p_plateau, eit_file): # voegt een nieuwe stap toe aan de trial_steps tabel in de database, met het id van de trial waar de stap bij hoort, het nummer van de stap, de PEEP waarde, de plateau druk waarde, het bestand van de EIT opname, en de datum en tijd van aanmaken. Als er een fout optreedt bij het toevoegen van de stap, wordt er een sqlite3.IntegrityError gegooid.
    with connect() as conn:
        conn.execute(
            "INSERT INTO trial_steps (trial_id, step_number, peep, p_plateau, eit_file, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (trial_id, step_number, peep, p_plateau, eit_file, _now()))

# ophalen van trials en stappen uit de database (bibliotheek)
def search_trials(query=""): # zoekt in de database naar trials waarvan het patient_number overeenkomt met de opgegeven query, en geeft een lijst van rijen terug met de id, patient_number, doctor, created_at en het aantal stappen van elke trial. De resultaten worden gesorteerd op created_at in aflopende volgorde. Als er geen query is opgegeven, worden alle trials teruggegeven. (dit krijg je te zien in de library view)
    with connect() as conn:
        return conn.execute(
            """SELECT t.id, t.patient_number, t.doctor, t.created_at,
                      (SELECT COUNT(*) FROM trial_steps s WHERE s.trial_id = t.id) AS n_steps
               FROM trials t WHERE t.patient_number LIKE ?
               ORDER BY t.created_at DESC""",
            (f"%{query}%",)).fetchall()

# ophalen van trials details
def get_trial(trial_id): # haalt de gegevens van een trial op uit de database, met het id van de trial als parameter. Geeft een rij terug met alle kolommen van de trial, of None als er geen trial is met het opgegeven id.
    with connect() as conn:
        return conn.execute("SELECT * FROM trials WHERE id = ?", (trial_id,)).fetchone()

# ophalen van trial stappen
def get_steps(trial_id): # haalt de stappen van een trial op uit de database, met het id van de trial als parameter. Geeft een lijst van rijen terug met alle kolommen van de stappen, gesorteerd op step_number in oplopende volgorde.
    with connect() as conn:
        return conn.execute("SELECT * FROM trial_steps WHERE trial_id = ? ORDER BY step_number",
                            (trial_id,)).fetchall()