import time
import serial
import os
from gtts import gTTS              # Βιβλιοθήκη για ελληνική φωνή
import pygame                      # Για την αναπαραγωγή του ήχου
from pyhuskylens import HuskyLens  # Βιβλιοθήκη HuskyLens

# ==========================================
# 1. ΑΡΧΙΚΟΠΟΙΗΣΗ HARDWARE & ΗΧΟΥ
# ==========================================
pygame.mixer.init()

# Αρχικοποίηση HuskyLens μέσω I2C
try:
    husky = HuskyLens(1)
    print("HuskyLens συνδέθηκε επιτυχώς!")
except Exception as e:
    print(f"Σφάλμα HuskyLens: {e}")
    husky = None

# Αρχικοποίηση L76K GPS Module μέσω Serial (UART)
try:
    # Στο Raspberry Pi, η default θύρα hardware serial είναι η /dev/ttyS0 ή /dev/ttyAMA0
    gps_serial = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=1)
    print("GPS Module L76K έτοιμο!")
except Exception as e:
    print(f"Σφάλμα σύνδεσης GPS: {e}")
    gps_serial = None

# Χαρτογράφηση HuskyLens IDs με αντικείμενα του δρόμου
HUSKY_ROAD_MAP = {
    1: "Διάβαση πεζών μπροστά σας.",
    2: "Φανάρι κυκλοφορίας.",
    3: "Προσοχή, εμπόδιο στο πεζοδρόμιο."
}

# ==========================================
# 2. ΛΕΙΤΟΥΡΓΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ
# ==========================================

def speak(text):
    """Μετατρέπει το κείμενο σε ελληνική ομιλία και το αναπαράγει"""
    print(f"[Φωνή]: {text}")
    try:
        # Δημιουργία αρχείου ήχου με ελληνική προφορά
        tts = gTTS(text=text, lang='el')
        tts.save("voice.mp3")
        
        # Αναπαραγωγή ήχου
        pygame.mixer.music.load("voice.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        # Καθαρισμός αρχείου
        os.remove("voice.mp3")
    except Exception as e:
        print(f"Σφάλμα ήχου: {e}")

def parse_gps_data():
    """
    Διαβάζει τη θύρα του GPS, αναζητά την εγγραφή $GNRMC ή $GNGGA 
    και επιστρέφει τις συντεταγμένες.
    """
    if gps_serial is None:
        return None, None
        
    try:
        line = gps_serial.readline().decode('ascii', errors='replace')
        # Το L76K στέλνει δεδομένα σε μορφή NMEA
        if "$GNRMC" in line or "$GPRMC" in line:
            parts = line.split(',')
            if parts[2] == 'A': # 'A' σημαίνει ότι το GPS έχει «κλειδώσει» σε δορυφόρους
                # Απλός υπολογισμός συντεταγμένων
                lat = parts[3]
                lon = parts[5]
                return lat, lon
    except Exception as e:
        print(f"Σφάλμα ανάγνωσης GPS: {e}")
    return None, None

def check_navigation(lat, lon):
    """
    Εικονική συνάρτηση πλοήγησης. 
    Συγκρίνει τη θέση του χρήστη με προκαθορισμένα σημεία (POI).
    """
    if lat and lon:
        # Στον πραγματικό διαγωνισμό, μπορείτε να βάλετε τις συντεταγμένες του σχολείου σας
        print(f"[GPS Position] Lat: {lat}, Lon: {lon}")
        # Παράδειγμα ειδοποίησης βάσει τοποθεσίας
        return "Βρίσκεστε στην οδό Κεντρικής Διαδρομής. Σε 50 μέτρα υπάρχει στροφή αριστερά."
    return None

# ==========================================
# 3. ΚΥΡΙΟΣ ΒΡΟΧΟΣ (MAIN LOOP)
# ==========================================
print("Το Έξυπνο Μπαστούνι τέθηκε σε λειτουργία!")
speak("Το σύστημα πλοήγησης ενεργοποιήθηκε.")

last_gps_check = 0
GPS_INTERVAL = 10 # Έλεγχος τοποθεσίας και οδηγιών κάθε 10 δευτερόλεπτα

try:
    while True:
        current_time = time.time()

        # ---------------------------------------------------------
        # Α. AI ΟΡΑΣΗ (HuskyLens) - ΑΜΕΣΗ ΠΡΟΤΕΡΑΙΟΤΗΤΑ
        # ---------------------------------------------------------
        if husky:
            try:
                blocks = husky.get_blocks()
                if blocks:
                    for block in blocks:
                        if block.id in HUSKY_ROAD_MAP:
                            # Το μπαστούνι μιλάει αμέσως αν δει φανάρι ή διάβαση
                            alert_text = HUSKY_ROAD_MAP[block.id]
                            speak(alert_text)
                            time.sleep(2) # Μικρή παύση για να μην επαναλαμβάνεται συνεχώς
            except Exception as e:
                print(f"Σφάλμα ανάγνωσης HuskyLens: {e}")

        # ---------------------------------------------------------
        # Β. ΓΕΩΕΝΤΟΠΙΣΜΟΣ & ΦΩΝΗΤΙΚΗ ΠΛΟΗΓΗΣΗ (L76K)
        # ---------------------------------------------------------
        if current_time - last_gps_check >= GPS_INTERVAL:
            lat, lon = parse_gps_data()
            
            # Αν βρεθεί σήμα, δώσε φωνητικές οδηγίες
            nav_instruction = check_navigation(lat, lon)
            if nav_instruction:
                speak(nav_instruction)
            
            last_gps_check = time.time()

        time.sleep(0.1) # Μικρή καθυστέρηση για εξοικονόμηση πόρων

except KeyboardInterrupt:
    print("\nΤο σύστημα απενεργοποιήθηκε.")
    speak("Το σύστημα απενεργοποιήθηκε.")
