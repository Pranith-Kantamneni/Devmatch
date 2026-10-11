"""Canonical directory of Indian colleges (campuses as separate entries).

Every entry has a stable ``id``. Users pick from this list so "VIT" and
"Vellore Institute of Technology" resolve to the same id and match.
Anything not listed can be entered as custom text — identical custom text
still matches via the ``custom:`` namespace.
"""

import re

_WS_RE = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _WS_RE.sub(" ", (text or "").strip().lower().replace(".", ""))


def _e(id, name, short, aliases, city, state):
    return {
        "id": id,
        "name": name,
        "short": short,
        "aliases": aliases,
        "city": city,
        "state": state,
    }


COLLEGES: list[dict] = [
    # ---- IITs ----
    _e("iit-bombay", "Indian Institute of Technology Bombay", "IIT Bombay", ["iit bombay", "iitb", "iit-bombay", "indian institute of technology bombay"], "Mumbai", "Maharashtra"),
    _e("iit-delhi", "Indian Institute of Technology Delhi", "IIT Delhi", ["iit delhi", "iitd", "iit-delhi", "indian institute of technology delhi"], "New Delhi", "Delhi"),
    _e("iit-madras", "Indian Institute of Technology Madras", "IIT Madras", ["iit madras", "iitm", "iit-madras", "indian institute of technology madras", "iit chennai"], "Chennai", "Tamil Nadu"),
    _e("iit-kanpur", "Indian Institute of Technology Kanpur", "IIT Kanpur", ["iit kanpur", "iitk", "indian institute of technology kanpur"], "Kanpur", "Uttar Pradesh"),
    _e("iit-kharagpur", "Indian Institute of Technology Kharagpur", "IIT Kharagpur", ["iit kharagpur", "iitkgp", "kgp", "indian institute of technology kharagpur"], "Kharagpur", "West Bengal"),
    _e("iit-roorkee", "Indian Institute of Technology Roorkee", "IIT Roorkee", ["iit roorkee", "iitr", "indian institute of technology roorkee"], "Roorkee", "Uttarakhand"),
    _e("iit-guwahati", "Indian Institute of Technology Guwahati", "IIT Guwahati", ["iit guwahati", "iitg", "indian institute of technology guwahati"], "Guwahati", "Assam"),
    _e("iit-hyderabad", "Indian Institute of Technology Hyderabad", "IIT Hyderabad", ["iit hyderabad", "iith", "indian institute of technology hyderabad"], "Hyderabad", "Telangana"),
    _e("iit-bhu", "Indian Institute of Technology (BHU) Varanasi", "IIT BHU", ["iit bhu", "iit varanasi", "iit(bhu)", "it bhu", "institute of technology bhu"], "Varanasi", "Uttar Pradesh"),
    _e("ism-dhanbad", "Indian Institute of Technology (ISM) Dhanbad", "IIT ISM Dhanbad", ["ism dhanbad", "iit ism", "iit dhanbad", "indian school of mines"], "Dhanbad", "Jharkhand"),
    _e("iit-indore", "Indian Institute of Technology Indore", "IIT Indore", ["iit indore", "iiti", "indian institute of technology indore"], "Indore", "Madhya Pradesh"),
    _e("iit-mandi", "Indian Institute of Technology Mandi", "IIT Mandi", ["iit mandi", "indian institute of technology mandi"], "Mandi", "Himachal Pradesh"),
    _e("iit-patna", "Indian Institute of Technology Patna", "IIT Patna", ["iit patna", "indian institute of technology patna"], "Patna", "Bihar"),
    _e("iit-ropar", "Indian Institute of Technology Ropar", "IIT Ropar", ["iit ropar", "iit ropar", "indian institute of technology ropar"], "Ropar", "Punjab"),
    _e("iit-jodhpur", "Indian Institute of Technology Jodhpur", "IIT Jodhpur", ["iit jodhpur", "indian institute of technology jodhpur"], "Jodhpur", "Rajasthan"),
    _e("iit-gandhinagar", "Indian Institute of Technology Gandhinagar", "IIT Gandhinagar", ["iit gandhinagar", "iitgn", "indian institute of technology gandhinagar"], "Gandhinagar", "Gujarat"),
    _e("iit-bhubaneswar", "Indian Institute of Technology Bhubaneswar", "IIT Bhubaneswar", ["iit bhubaneswar", "iitbbs", "indian institute of technology bhubaneswar"], "Bhubaneswar", "Odisha"),
    _e("iit-palakkad", "Indian Institute of Technology Palakkad", "IIT Palakkad", ["iit palakkad", "indian institute of technology palakkad"], "Palakkad", "Kerala"),
    _e("iit-tirupati", "Indian Institute of Technology Tirupati", "IIT Tirupati", ["iit tirupati", "indian institute of technology tirupati"], "Tirupati", "Andhra Pradesh"),
    _e("iit-jammu", "Indian Institute of Technology Jammu", "IIT Jammu", ["iit jammu", "indian institute of technology jammu"], "Jammu", "Jammu and Kashmir"),
    _e("iit-dharwad", "Indian Institute of Technology Dharwad", "IIT Dharwad", ["iit dharwad", "indian institute of technology dharwad"], "Dharwad", "Karnataka"),
    _e("iit-bhilai", "Indian Institute of Technology Bhilai", "IIT Bhilai", ["iit bhilai", "indian institute of technology bhilai"], "Bhilai", "Chhattisgarh"),
    _e("iit-goa", "Indian Institute of Technology Goa", "IIT Goa", ["iit goa", "indian institute of technology goa"], "Ponda", "Goa"),
    # ---- NITs ----
    _e("nit-trichy", "National Institute of Technology Tiruchirappalli", "NIT Trichy", ["nit trichy", "nitt", "nit tiruchirappalli", "nit tiruchy", "national institute of technology tiruchirappalli"], "Tiruchirappalli", "Tamil Nadu"),
    _e("nit-surathkal", "National Institute of Technology Karnataka, Surathkal", "NIT Surathkal", ["nit surathkal", "nitk", "nit karnataka", "national institute of technology karnataka"], "Mangalore", "Karnataka"),
    _e("nit-warangal", "National Institute of Technology Warangal", "NIT Warangal", ["nit warangal", "nitw", "national institute of technology warangal"], "Warangal", "Telangana"),
    _e("nit-calicut", "National Institute of Technology Calicut", "NIT Calicut", ["nit calicut", "nitc", "nit kozhikode", "national institute of technology calicut"], "Kozhikode", "Kerala"),
    _e("nit-rourkela", "National Institute of Technology Rourkela", "NIT Rourkela", ["nit rourkela", "nitrkl", "national institute of technology rourkela"], "Rourkela", "Odisha"),
    _e("vnit-nagpur", "Visvesvaraya National Institute of Technology Nagpur", "VNIT Nagpur", ["vnit", "vnit nagpur", "nit nagpur", "visvesvaraya national institute of technology"], "Nagpur", "Maharashtra"),
    _e("nit-durgapur", "National Institute of Technology Durgapur", "NIT Durgapur", ["nit durgapur", "nitd", "national institute of technology durgapur"], "Durgapur", "West Bengal"),
    _e("nit-jamshedpur", "National Institute of Technology Jamshedpur", "NIT Jamshedpur", ["nit jamshedpur", "nit jsr", "national institute of technology jamshedpur"], "Jamshedpur", "Jharkhand"),
    _e("nit-jalandhar", "Dr. B. R. Ambedkar National Institute of Technology Jalandhar", "NIT Jalandhar", ["nit jalandhar", "nitj", "national institute of technology jalandhar"], "Jalandhar", "Punjab"),
    _e("mnnit-allahabad", "Motilal Nehru National Institute of Technology Allahabad", "MNNIT Allahabad", ["mnnit", "mnnit allahabad", "nit allahabad", "mnnit prayagraj", "motilal nehru nit"], "Prayagraj", "Uttar Pradesh"),
    _e("manit-bhopal", "Maulana Azad National Institute of Technology Bhopal", "MANIT Bhopal", ["manit", "manit bhopal", "nit bhopal", "maulana azad nit"], "Bhopal", "Madhya Pradesh"),
    _e("mnit-jaipur", "Malaviya National Institute of Technology Jaipur", "MNIT Jaipur", ["mnit", "mnit jaipur", "nit jaipur", "malaviya nit"], "Jaipur", "Rajasthan"),
    _e("svnit-surat", "Sardar Vallabhbhai National Institute of Technology Surat", "SVNIT Surat", ["svnit", "svnit surat", "nit surat", "sardar vallabhbhai nit"], "Surat", "Gujarat"),
    _e("nit-kurukshetra", "National Institute of Technology Kurukshetra", "NIT Kurukshetra", ["nit kurukshetra", "nit kkr", "national institute of technology kurukshetra"], "Kurukshetra", "Haryana"),
    _e("nit-hamirpur", "National Institute of Technology Hamirpur", "NIT Hamirpur", ["nit hamirpur", "nith", "national institute of technology hamirpur"], "Hamirpur", "Himachal Pradesh"),
    _e("nit-silchar", "National Institute of Technology Silchar", "NIT Silchar", ["nit silchar", "nits", "national institute of technology silchar"], "Silchar", "Assam"),
    _e("nit-srinagar", "National Institute of Technology Srinagar", "NIT Srinagar", ["nit srinagar", "nitsri", "national institute of technology srinagar"], "Srinagar", "Jammu and Kashmir"),
    _e("nit-raipur", "National Institute of Technology Raipur", "NIT Raipur", ["nit raipur", "nitrr", "national institute of technology raipur"], "Raipur", "Chhattisgarh"),
    _e("nit-agartala", "National Institute of Technology Agartala", "NIT Agartala", ["nit agartala", "nita", "national institute of technology agartala"], "Agartala", "Tripura"),
    _e("nit-patna", "National Institute of Technology Patna", "NIT Patna", ["nit patna", "nitp", "national institute of technology patna", "bihar college of engineering"], "Patna", "Bihar"),
    _e("nit-puducherry", "National Institute of Technology Puducherry", "NIT Puducherry", ["nit puducherry", "nit pondicherry", "nit py"], "Karaikal", "Puducherry"),
    _e("nit-meghalaya", "National Institute of Technology Meghalaya", "NIT Meghalaya", ["nit meghalaya", "nitm", "national institute of technology meghalaya"], "Shillong", "Meghalaya"),
    _e("nit-manipur", "National Institute of Technology Manipur", "NIT Manipur", ["nit manipur", "national institute of technology manipur"], "Imphal", "Manipur"),
    _e("nit-mizoram", "National Institute of Technology Mizoram", "NIT Mizoram", ["nit mizoram", "national institute of technology mizoram"], "Aizawl", "Mizoram"),
    _e("nit-nagaland", "National Institute of Technology Nagaland", "NIT Nagaland", ["nit nagaland", "nitn", "national institute of technology nagaland"], "Dimapur", "Nagaland"),
    _e("nit-sikkim", "National Institute of Technology Sikkim", "NIT Sikkim", ["nit sikkim", "national institute of technology sikkim"], "Ravangla", "Sikkim"),
    _e("nit-arunachal", "National Institute of Technology Arunachal Pradesh", "NIT Arunachal Pradesh", ["nit arunachal", "nit itanagar", "national institute of technology arunachal pradesh"], "Yupia", "Arunachal Pradesh"),
    _e("nit-uttarakhand", "National Institute of Technology Uttarakhand", "NIT Uttarakhand", ["nit uttarakhand", "nit uk", "national institute of technology uttarakhand"], "Srinagar (Garhwal)", "Uttarakhand"),
    _e("nit-delhi", "National Institute of Technology Delhi", "NIT Delhi", ["nit delhi", "national institute of technology delhi"], "New Delhi", "Delhi"),
    _e("nit-goa", "National Institute of Technology Goa", "NIT Goa", ["nit goa", "national institute of technology goa"], "Ponda", "Goa"),
    _e("nit-andhra", "National Institute of Technology Andhra Pradesh", "NIT Andhra Pradesh", ["nit andhra", "nit tadepalligudem", "national institute of technology andhra pradesh"], "Tadepalligudem", "Andhra Pradesh"),
    _e("iiest-shibpur", "Indian Institute of Engineering Science and Technology Shibpur", "IIEST Shibpur", ["iiest", "iiest shibpur", "iiest howrah", "bengal engineering college", "becollege"], "Howrah", "West Bengal"),
    # ---- IIITs ----
    _e("iiit-hyderabad", "International Institute of Information Technology Hyderabad", "IIIT Hyderabad", ["iiit hyderabad", "iiith", "iiit-h", "international institute of information technology hyderabad"], "Hyderabad", "Telangana"),
    _e("iiit-bangalore", "International Institute of Information Technology Bangalore", "IIIT Bangalore", ["iiit bangalore", "iiitb", "iiit-b", "international institute of information technology bangalore"], "Bangalore", "Karnataka"),
    _e("iiit-delhi", "Indraprastha Institute of Information Technology Delhi", "IIIT Delhi", ["iiit delhi", "iiitd", "iiit-d", "indraprastha institute of information technology"], "New Delhi", "Delhi"),
    _e("iiit-allahabad", "Indian Institute of Information Technology Allahabad", "IIIT Allahabad", ["iiit allahabad", "iiita", "iiit prayagraj", "indian institute of information technology allahabad"], "Prayagraj", "Uttar Pradesh"),
    _e("iiitm-gwalior", "Indian Institute of Information Technology and Management Gwalior", "IIITM Gwalior", ["iiitm", "iiitm gwalior", "iiit gwalior", "abv-iiitm"], "Gwalior", "Madhya Pradesh"),
    _e("iiitdm-jabalpur", "Indian Institute of Information Technology, Design and Manufacturing Jabalpur", "IIITDM Jabalpur", ["iiitdm", "iiitdm jabalpur", "iiit jabalpur", "pdp m"], "Jabalpur", "Madhya Pradesh"),
    _e("iiitdm-kancheepuram", "Indian Institute of Information Technology, Design and Manufacturing Kancheepuram", "IIITDM Kanchipuram", ["iiitdm kancheepuram", "iiitdm kanchipuram", "iiit kancheepuram", "iiit chennai"], "Chennai", "Tamil Nadu"),
    _e("iiit-sricity", "Indian Institute of Information Technology Sri City", "IIIT Sri City", ["iiit sri city", "iiit sricity", "iiit chittoor"], "Sri City", "Andhra Pradesh"),
    _e("iiit-guwahati", "Indian Institute of Information Technology Guwahati", "IIIT Guwahati", ["iiit guwahati", "indian institute of information technology guwahati"], "Guwahati", "Assam"),
    _e("iiit-vadodara", "Indian Institute of Information Technology Vadodara", "IIIT Vadodara", ["iiit vadodara", "iiit baroda", "indian institute of information technology vadodara"], "Vadodara", "Gujarat"),
    _e("iiit-surat", "Indian Institute of Information Technology Surat", "IIIT Surat", ["iiit surat", "indian institute of information technology surat"], "Surat", "Gujarat"),
    _e("iiit-bhopal", "Indian Institute of Information Technology Bhopal", "IIIT Bhopal", ["iiit bhopal", "indian institute of information technology bhopal"], "Bhopal", "Madhya Pradesh"),
    _e("iiit-nagpur", "Indian Institute of Information Technology Nagpur", "IIIT Nagpur", ["iiit nagpur", "indian institute of information technology nagpur"], "Nagpur", "Maharashtra"),
    _e("iiit-pune", "Indian Institute of Information Technology Pune", "IIIT Pune", ["iiit pune", "indian institute of information technology pune"], "Pune", "Maharashtra"),
    _e("iiit-ranchi", "Indian Institute of Information Technology Ranchi", "IIIT Ranchi", ["iiit ranchi", "indian institute of information technology ranchi"], "Ranchi", "Jharkhand"),
    _e("iiit-dharwad", "Indian Institute of Information Technology Dharwad", "IIIT Dharwad", ["iiit dharwad", "indian institute of information technology dharwad"], "Dharwad", "Karnataka"),
    _e("iiit-kottayam", "Indian Institute of Information Technology Kottayam", "IIIT Kottayam", ["iiit kottayam", "indian institute of information technology kottayam"], "Kottayam", "Kerala"),
    _e("iiit-kalyani", "Indian Institute of Information Technology Kalyani", "IIIT Kalyani", ["iiit kalyani", "indian institute of information technology kalyani"], "Kalyani", "West Bengal"),
    _e("iiit-lucknow", "Indian Institute of Information Technology Lucknow", "IIIT Lucknow", ["iiit lucknow", "indian institute of information technology lucknow"], "Lucknow", "Uttar Pradesh"),
    _e("iiit-manipur", "Indian Institute of Information Technology Manipur", "IIIT Manipur", ["iiit manipur", "iiit imphal", "indian institute of information technology manipur"], "Imphal", "Manipur"),
    _e("iiit-trichy", "Indian Institute of Information Technology Tiruchirappalli", "IIIT Trichy", ["iiit trichy", "iiit tiruchirappalli", "indian institute of information technology tiruchirappalli"], "Tiruchirappalli", "Tamil Nadu"),
    _e("iiit-una", "Indian Institute of Information Technology Una", "IIIT Una", ["iiit una", "indian institute of information technology una"], "Una", "Himachal Pradesh"),
    _e("iiit-kota", "Indian Institute of Information Technology Kota", "IIIT Kota", ["iiit kota", "indian institute of information technology kota"], "Kota", "Rajasthan"),
    _e("iiit-sonepat", "Indian Institute of Information Technology Sonepat", "IIIT Sonepat", ["iiit sonepat", "iiit sonipat", "indian institute of information technology sonepat"], "Sonepat", "Haryana"),
    _e("iiit-agartala", "Indian Institute of Information Technology Agartala", "IIIT Agartala", ["iiit agartala", "indian institute of information technology agartala"], "Agartala", "Tripura"),
    _e("iiit-bhagalpur", "Indian Institute of Information Technology Bhagalpur", "IIIT Bhagalpur", ["iiit bhagalpur", "indian institute of information technology bhagalpur"], "Bhagalpur", "Bihar"),
    _e("iiit-raichur", "Indian Institute of Information Technology Raichur", "IIIT Raichur", ["iiit raichur", "indian institute of information technology raichur"], "Raichur", "Karnataka"),
    _e("iiit-kurnool", "Indian Institute of Information Technology Design and Manufacturing Kurnool", "IIITDM Kurnool", ["iiit kurnool", "iiitdm kurnool", "indian institute of information technology kurnool"], "Kurnool", "Andhra Pradesh"),
    _e("iiit-bhubaneswar", "International Institute of Information Technology Bhubaneswar", "IIIT Bhubaneswar", ["iiit bhubaneswar", "iiit-bh", "international institute of information technology bhubaneswar"], "Bhubaneswar", "Odisha"),
    # ---- BITS ----
    _e("bits-pilani", "Birla Institute of Technology and Science, Pilani", "BITS Pilani", ["bits", "bits pilani", "bits-pilani", "birla institute of technology and science pilani"], "Pilani", "Rajasthan"),
    _e("bits-goa", "Birla Institute of Technology and Science, Pilani – K. K. Birla Goa Campus", "BITS Goa", ["bits goa", "bits-pilani goa", "bits goa campus", "kk birla goa"], "Vasco da Gama", "Goa"),
    _e("bits-hyderabad", "Birla Institute of Technology and Science, Pilani – Hyderabad Campus", "BITS Hyderabad", ["bits hyderabad", "bits hyd", "bits-pilani hyderabad", "bits hyderabad campus"], "Hyderabad", "Telangana"),
    # ---- GFTIs / other central ----
    _e("bit-mesra", "Birla Institute of Technology Mesra", "BIT Mesra", ["bit mesra", "bit ranchi", "birla institute of technology mesra"], "Ranchi", "Jharkhand"),
    _e("tezpur-university", "Tezpur University", "Tezpur University", ["tezpur university", "tu tezpur"], "Tezpur", "Assam"),
    _e("assam-university", "Assam University, Silchar", "Assam University", ["assam university", "assam university silchar", "aus silchar"], "Silchar", "Assam"),
    _e("pec-puducherry", "Pondicherry Engineering College", "PEC Puducherry", ["pec", "pec puducherry", "pec pondicherry", "pondicherry engineering college", "ptuniv"], "Puducherry", "Puducherry"),
    _e("gurukula-kangri", "Gurukula Kangri Vishwavidyalaya", "Gurukula Kangri", ["gurukula kangri", "gurukul kangri", "gkv haridwar"], "Haridwar", "Uttarakhand"),
    _e("dayalbagh-agra", "Dayalbagh Educational Institute", "Dayalbagh Educational Institute", ["dayalbagh", "dei agra", "dayalbagh educational institute"], "Agra", "Uttar Pradesh"),
    _e("thapar-patiala", "Thapar Institute of Engineering and Technology", "Thapar Patiala", ["thapar", "thapar patiala", "tiet", "tiet patiala", "thapar institute"], "Patiala", "Punjab"),
    _e("spa-delhi", "School of Planning and Architecture Delhi", "SPA Delhi", ["spa delhi", "school of planning and architecture delhi"], "New Delhi", "Delhi"),
    # ---- Tamil Nadu ----
    _e("anna-ceg", "College of Engineering, Guindy (Anna University)", "CEG Guindy", ["ceg", "ceg guindy", "college of engineering guindy", "anna university guindy", "guindy engineering college"], "Chennai", "Tamil Nadu"),
    _e("anna-mit", "Madras Institute of Technology, Chromepet (Anna University)", "MIT Chromepet", ["mit chromepet", "madras institute of technology", "mit chennai", "mit anna university"], "Chennai", "Tamil Nadu"),
    _e("anna-act", "Alagappa College of Technology (Anna University)", "ACT Chennai", ["act chennai", "alagappa college of technology", "act guindy"], "Chennai", "Tamil Nadu"),
    _e("psg-coimbatore", "PSG College of Technology", "PSG Tech", ["psg", "psg tech", "psg college of technology", "psg coimbatore"], "Coimbatore", "Tamil Nadu"),
    _e("cit-coimbatore", "Coimbatore Institute of Technology", "CIT Coimbatore", ["cit coimbatore", "cit", "coimbatore institute of technology"], "Coimbatore", "Tamil Nadu"),
    _e("tce-madurai", "Thiagarajar College of Engineering", "TCE Madurai", ["tce", "tce madurai", "thiagarajar college of engineering"], "Madurai", "Tamil Nadu"),
    _e("ssn-chennai", "Sri Sivasubramaniya Nadar College of Engineering", "SSN College", ["ssn", "ssn chennai", "ssn college of engineering", "sri sivasubramaniya nadar"], "Chennai", "Tamil Nadu"),
    _e("svce-chennai", "Sri Venkateswara College of Engineering", "SVCE Chennai", ["svce", "svce chennai", "sri venkateswara college of engineering sriperumbudur"], "Sriperumbudur", "Tamil Nadu"),
    _e("rajalakshmi-chennai", "Rajalakshmi Engineering College", "Rajalakshmi Engineering College", ["rajalakshmi", "rec chennai", "rajalakshmi engineering college"], "Chennai", "Tamil Nadu"),
    _e("stjoseph-chennai", "St. Joseph's College of Engineering", "St. Joseph's Chennai", ["st josephs", "st joseph college of engineering", "st josephs chennai"], "Chennai", "Tamil Nadu"),
    _e("panimalar-chennai", "Panimalar Engineering College", "Panimalar", ["panimalar", "panimalar engineering college"], "Chennai", "Tamil Nadu"),
    _e("velammal-chennai", "Velammal Engineering College", "Velammal", ["velammal", "velammal engineering college"], "Chennai", "Tamil Nadu"),
    _e("sona-salem", "Sona College of Technology", "Sona College", ["sona", "sona salem", "sona college of technology"], "Salem", "Tamil Nadu"),
    _e("kumaraguru-coimbatore", "Kumaraguru College of Technology", "KCT Coimbatore", ["kct", "kumaraguru", "kumaraguru college of technology"], "Coimbatore", "Tamil Nadu"),
    _e("bannari-sathy", "Bannari Amman Institute of Technology", "BIT Sathy", ["bannari", "bit sathy", "bannari amman institute of technology"], "Sathyamangalam", "Tamil Nadu"),
    _e("kongu-erode", "Kongu Engineering College", "Kongu Engineering College", ["kongu", "kec erode", "kongu engineering college"], "Erode", "Tamil Nadu"),
    _e("mepco-sivakasi", "Mepco Schlenk Engineering College", "Mepco Schlenk", ["mepco", "mepco sivakasi", "mepco schlenk engineering college"], "Sivakasi", "Tamil Nadu"),
    _e("kalasalingam", "Kalasalingam Academy of Research and Education", "Kalasalingam", ["kalasalingam", "kare", "kalasalingam university"], "Krishnankoil", "Tamil Nadu"),
    _e("sastra-thanjavur", "SASTRA Deemed University", "SASTRA", ["sastra", "sastra thanjavur", "sastra university", "shanmugha arts"], "Thanjavur", "Tamil Nadu"),
    _e("vit-vellore", "Vellore Institute of Technology, Vellore", "VIT Vellore", ["vit", "vit vellore", "vellore institute of technology", "vit university vellore"], "Vellore", "Tamil Nadu"),
    _e("vit-chennai", "Vellore Institute of Technology, Chennai", "VIT Chennai", ["vit chennai", "vit chennai campus", "vellore institute of technology chennai"], "Chennai", "Tamil Nadu"),
    _e("vit-bhopal", "Vellore Institute of Technology, Bhopal", "VIT Bhopal", ["vit bhopal", "vit bhopal campus", "vellore institute of technology bhopal"], "Bhopal", "Madhya Pradesh"),
    _e("vit-ap", "Vellore Institute of Technology, Andhra Pradesh", "VIT-AP", ["vit ap", "vit amaravati", "vit andhra pradesh", "vellore institute of technology ap"], "Amaravati", "Andhra Pradesh"),
    _e("srm-ktr", "SRM Institute of Science and Technology, Kattankulathur", "SRM Kattankulathur", ["srm", "srm ktr", "srm chennai", "srm kattankulathur", "srm institute of science and technology"], "Chennai", "Tamil Nadu"),
    _e("srm-ramapuram", "SRM Institute of Science and Technology, Ramapuram", "SRM Ramapuram", ["srm ramapuram", "srm ramapuram campus"], "Chennai", "Tamil Nadu"),
    _e("srm-vadapalani", "SRM Institute of Science and Technology, Vadapalani", "SRM Vadapalani", ["srm vadapalani", "srm vadapalani campus"], "Chennai", "Tamil Nadu"),
    _e("srm-ncr", "SRM Institute of Science and Technology, Delhi NCR", "SRM NCR", ["srm ncr", "srm ghaziabad", "srm delhi ncr", "srm modinagar"], "Ghaziabad", "Uttar Pradesh"),
    _e("srm-ap", "SRM University, Andhra Pradesh", "SRM AP", ["srm ap", "srm amaravati", "srm university ap"], "Amaravati", "Andhra Pradesh"),
    _e("srm-haryana", "SRM University, Haryana", "SRM Haryana", ["srm haryana", "srm sonepat", "srm university haryana"], "Sonepat", "Haryana"),
    _e("snu-chennai", "Shiv Nadar University, Chennai", "Shiv Nadar Chennai", ["snu chennai", "shiv nadar chennai", "snuchennai"], "Chennai", "Tamil Nadu"),
    _e("hindustan-chennai", "Hindustan Institute of Technology and Science", "HITS Chennai", ["hits", "hindustan", "hindustan university", "hits chennai"], "Chennai", "Tamil Nadu"),
    _e("crescent-chennai", "B.S. Abdur Rahman Crescent Institute of Science and Technology", "Crescent Chennai", ["crescent", "bsa crescent", "crescent institute"], "Chennai", "Tamil Nadu"),
    _e("saveetha-chennai", "Saveetha Engineering College", "Saveetha", ["saveetha", "saveetha engineering college", "sec chennai"], "Chennai", "Tamil Nadu"),
    _e("sathyabama-chennai", "Sathyabama Institute of Science and Technology", "Sathyabama", ["sathyabama", "sathyabama university", "sathyabama institute"], "Chennai", "Tamil Nadu"),
    _e("bharath-chennai", "Bharath Institute of Higher Education and Research", "Bharath University", ["bharath", "bharath university", "bharath institute chennai"], "Chennai", "Tamil Nadu"),
    _e("mgr-chennai", "Dr. M.G.R. Educational and Research Institute", "Dr. MGR University", ["mgr", "mgr university", "dr mgr educational"], "Chennai", "Tamil Nadu"),
    _e("karunya-coimbatore", "Karunya Institute of Technology and Sciences", "Karunya", ["karunya", "karunya coimbatore", "karunya institute"], "Coimbatore", "Tamil Nadu"),
    _e("amrita-coimbatore", "Amrita School of Engineering, Coimbatore", "Amrita Coimbatore", ["amrita coimbatore", "amrita school of engineering coimbatore", "amrita vishwa"], "Coimbatore", "Tamil Nadu"),
    _e("amrita-chennai", "Amrita School of Engineering, Chennai", "Amrita Chennai", ["amrita chennai", "amrita chennai campus"], "Chennai", "Tamil Nadu"),
    _e("amrita-bangalore", "Amrita School of Engineering, Bengaluru", "Amrita Bengaluru", ["amrita bangalore", "amrita bengaluru"], "Bangalore", "Karnataka"),
    _e("amrita-amritapuri", "Amrita School of Engineering, Amritapuri", "Amrita Amritapuri", ["amrita amritapuri", "amrita kerala"], "Kollam", "Kerala"),
    _e("gct-coimbatore", "Government College of Technology Coimbatore", "GCT Coimbatore", ["gct", "gct coimbatore", "government college of technology coimbatore"], "Coimbatore", "Tamil Nadu"),
    _e("gce-salem", "Government College of Engineering Salem", "GCE Salem", ["gce salem", "government college of engineering salem"], "Salem", "Tamil Nadu"),
    _e("gce-bargur", "Government College of Engineering Bargur", "GCE Bargur", ["gce bargur", "government college of engineering bargur"], "Bargur", "Tamil Nadu"),
    # ---- Karnataka ----
    _e("rvce-bangalore", "R.V. College of Engineering", "RVCE", ["rvce", "rv college of engineering", "r v college of engineering"], "Bangalore", "Karnataka"),
    _e("bmsce-bangalore", "BMS College of Engineering", "BMSCE", ["bmsce", "bms college of engineering", "bmsce bangalore"], "Bangalore", "Karnataka"),
    _e("msrit-bangalore", "M.S. Ramaiah Institute of Technology", "MSRIT", ["msrit", "ms ramaiah", "ramaiah institute of technology", "msrit bangalore"], "Bangalore", "Karnataka"),
    _e("pes-bangalore", "PES University", "PES University", ["pes", "pes university", "pesu", "pesit", "pes institute of technology"], "Bangalore", "Karnataka"),
    _e("bit-bangalore", "Bangalore Institute of Technology", "BIT Bangalore", ["bit bangalore", "bangalore institute of technology"], "Bangalore", "Karnataka"),
    _e("dsce-bangalore", "Dayananda Sagar College of Engineering", "DSCE", ["dsce", "dayananda sagar", "dsce bangalore", "dayananda sagar college of engineering"], "Bangalore", "Karnataka"),
    _e("dsu-bangalore", "Dayananda Sagar University", "DSU", ["dsu", "dayananda sagar university"], "Bangalore", "Karnataka"),
    _e("cmrit-bangalore", "CMR Institute of Technology", "CMRIT", ["cmrit", "cmr institute of technology", "cmrit bangalore"], "Bangalore", "Karnataka"),
    _e("bmsit-bangalore", "BMS Institute of Technology and Management", "BMSIT", ["bmsit", "bms institute of technology", "bmsit bangalore"], "Bangalore", "Karnataka"),
    _e("rnsit-bangalore", "RNS Institute of Technology", "RNSIT", ["rnsit", "rns institute of technology"], "Bangalore", "Karnataka"),
    _e("nmit-bangalore", "Nitte Meenakshi Institute of Technology", "NMIT", ["nmit", "nitte meenakshi", "nmit bangalore"], "Bangalore", "Karnataka"),
    _e("jssate-bangalore", "JSS Academy of Technical Education, Bengaluru", "JSSATE Bengaluru", ["jssate", "jss bangalore", "jss academy bangalore"], "Bangalore", "Karnataka"),
    _e("acharya-bangalore", "Acharya Institute of Technology", "Acharya IT", ["acharya", "acharya institute of technology", "ait bangalore"], "Bangalore", "Karnataka"),
    _e("reva-bangalore", "Reva University", "Reva University", ["reva", "reva university", "ru bangalore"], "Bangalore", "Karnataka"),
    _e("presidency-bangalore", "Presidency University, Bengaluru", "Presidency Bengaluru", ["presidency bangalore", "presidency university bangalore"], "Bangalore", "Karnataka"),
    _e("alliance-bangalore", "Alliance University", "Alliance University", ["alliance", "alliance university", "alliance bangalore"], "Bangalore", "Karnataka"),
    _e("christ-bangalore", "Christ University, Bengaluru", "Christ Bengaluru", ["christ", "christ university", "christ bangalore", "christ deemed university"], "Bangalore", "Karnataka"),
    _e("jain-bangalore", "Jain University, Bengaluru", "Jain University", ["jain", "jain university", "ju bangalore", "jain deemed university"], "Bangalore", "Karnataka"),
    _e("uvce-bangalore", "University Visvesvaraya College of Engineering", "UVCE", ["uvce", "university visvesvaraya college of engineering", "uvce bangalore"], "Bangalore", "Karnataka"),
    _e("nie-mysore", "National Institute of Engineering, Mysuru", "NIE Mysuru", ["nie", "nie mysore", "nie mysuru", "national institute of engineering"], "Mysuru", "Karnataka"),
    _e("sjce-mysore", "JSS Science and Technology University (SJCE)", "SJCE Mysuru", ["sjce", "sjce mysore", "sri jayachamarajendra college of engineering", "jss stu"], "Mysuru", "Karnataka"),
    _e("sit-tumkur", "Siddaganga Institute of Technology", "SIT Tumkur", ["sit tumkur", "sit tumakuru", "siddaganga institute of technology"], "Tumakuru", "Karnataka"),
    _e("bec-bagalkot", "Basaveshwar Engineering College", "BEC Bagalkot", ["bec bagalkot", "basaveshwar engineering college", "bec bgk"], "Bagalkot", "Karnataka"),
    _e("kletech-hubli", "KLE Technological University", "KLE Tech", ["kletech", "kle tech", "kle technological university", "bvb hubli", "kle hubli"], "Hubballi", "Karnataka"),
    _e("nmam-nitte", "NMAM Institute of Technology, Nitte", "NMAMIT", ["nmam", "nmamit", "nmam nitte", "nitte institute"], "Nitte", "Karnataka"),
    _e("mit-manipal", "Manipal Institute of Technology", "MIT Manipal", ["mit manipal", "manipal institute of technology", "manipal", "mit mahe"], "Manipal", "Karnataka"),
    _e("mit-jaipur", "Manipal University Jaipur (MUJ)", "Manipal Jaipur", ["manipal jaipur", "muj", "manipal university jaipur"], "Jaipur", "Rajasthan"),
    _e("smit-sikkim", "Sikkim Manipal Institute of Technology", "SMIT", ["smit", "smit sikkim", "sikkim manipal institute of technology"], "Majitar", "Sikkim"),
    _e("mahe-bangalore", "Manipal Academy of Higher Education, Bengaluru", "MAHE Bengaluru", ["mahe bangalore", "mahe bengaluru", "manipal bangalore"], "Bangalore", "Karnataka"),
    _e("iisc-bangalore", "Indian Institute of Science", "IISc", ["iisc", "iisc bangalore", "indian institute of science"], "Bangalore", "Karnataka"),
    # ---- Maharashtra (Mumbai / Pune / Nagpur) ----
    _e("vjti-mumbai", "Veermata Jijabai Technological Institute", "VJTI Mumbai", ["vjti", "vjti mumbai", "veermata jijabai technological institute"], "Mumbai", "Maharashtra"),
    _e("spit-mumbai", "Sardar Patel Institute of Technology", "SPIT Mumbai", ["spit", "spit mumbai", "sardar patel institute of technology"], "Mumbai", "Maharashtra"),
    _e("spce-mumbai", "Sardar Patel College of Engineering", "SPCE Mumbai", ["spce", "spce mumbai", "sardar patel college of engineering"], "Mumbai", "Maharashtra"),
    _e("djscoe-mumbai", "Dwarkadas J. Sanghvi College of Engineering", "DJ Sanghvi", ["dj sanghvi", "djscoe", "d j sanghvi", "dwarkadas sanghvi"], "Mumbai", "Maharashtra"),
    _e("tsec-mumbai", "Thadomal Shahani Engineering College", "TSEC Mumbai", ["tsec", "thadomal", "thadomal shahani", "tsec bandra"], "Mumbai", "Maharashtra"),
    _e("vesit-mumbai", "Vivekanand Education Society Institute of Technology", "VESIT Mumbai", ["vesit", "vesit mumbai", "vivekanand institute of technology chem bur"], "Mumbai", "Maharashtra"),
    _e("kjsomaiya-mumbai", "K. J. Somaiya College of Engineering", "KJ Somaiya", ["kj somaiya", "kjsce", "k j somaiya college of engineering", "somaiya vidyavihar"], "Mumbai", "Maharashtra"),
    _e("crce-mumbai", "Fr. Conceicao Rodrigues College of Engineering", "Fr. CRCE", ["crce", "fr crce", "fr agnel bandra", "conceicao rodrigues"], "Mumbai", "Maharashtra"),
    _e("rizvi-mumbai", "Rizvi College of Engineering", "Rizvi COE", ["rizvi", "rizvi college of engineering", "rizvi bandra"], "Mumbai", "Maharashtra"),
    _e("tcet-mumbai", "Thakur College of Engineering and Technology", "TCET Mumbai", ["tcet", "thakur college", "tcet kandivali"], "Mumbai", "Maharashtra"),
    _e("sakec-mumbai", "Shah and Anchor Kutchhi Engineering College", "SAKEC", ["sakec", "shah and anchor", "sakec chembur"], "Mumbai", "Maharashtra"),
    _e("vit-wadala", "Vidyalankar Institute of Technology", "VIT Wadala", ["vit wadala", "vidyalankar", "vidyalankar institute of technology"], "Mumbai", "Maharashtra"),
    _e("xie-mumbai", "Xavier Institute of Engineering", "XIE Mahim", ["xie", "xavier institute of engineering", "xie mahim"], "Mumbai", "Maharashtra"),
    _e("ict-mumbai", "Institute of Chemical Technology Mumbai", "ICT Mumbai", ["ict", "ict mumbai", "udct", "institute of chemical technology"], "Mumbai", "Maharashtra"),
    _e("nmims-mumbai", "NMIMS Mukesh Patel School of Technology Management and Engineering", "NMIMS Mumbai", ["nmims", "nmims mumbai", "mpstme", "mukesh patel school"], "Mumbai", "Maharashtra"),
    _e("nmims-shirpur", "NMIMS Shirpur Campus", "NMIMS Shirpur", ["nmims shirpur", "nmims shirpur campus"], "Shirpur", "Maharashtra"),
    _e("mithibai-mumbai", "Mithibai College", "Mithibai", ["mithibai", "mithibai college", "mithibai vile parle"], "Mumbai", "Maharashtra"),
    _e("jaihind-mumbai", "Jai Hind College", "Jai Hind", ["jai hind", "jai hind college", "jai hind churchgate"], "Mumbai", "Maharashtra"),
    _e("xaviers-mumbai", "St. Xavier's College Mumbai", "St. Xavier's Mumbai", ["xaviers mumbai", "st xaviers mumbai", "st xaviers college mumbai"], "Mumbai", "Maharashtra"),
    _e("coep-pune", "COEP Technological University", "COEP Pune", ["coep", "coep pune", "college of engineering pune"], "Pune", "Maharashtra"),
    _e("pict-pune", "Pune Institute of Computer Technology", "PICT Pune", ["pict", "pict pune", "pune institute of computer technology"], "Pune", "Maharashtra"),
    _e("vit-pune", "Vishwakarma Institute of Technology, Pune", "VIT Pune", ["vit pune", "vishwakarma institute of technology", "vit bibwewadi"], "Pune", "Maharashtra"),
    _e("viit-pune", "Vishwakarma Institute of Information Technology", "VIIT Pune", ["viit", "viit pune", "vishwakarma institute of information technology"], "Pune", "Maharashtra"),
    _e("mitwpu-pune", "MIT World Peace University", "MIT-WPU", ["mitwpu", "mit wpu", "mit world peace university", "mit pune"], "Pune", "Maharashtra"),
    _e("sit-pune", "Symbiosis Institute of Technology", "SIT Pune", ["sit pune", "symbiosis institute of technology"], "Pune", "Maharashtra"),
    _e("scit-pune", "Symbiosis Centre for Information Technology", "SCIT Pune", ["scit", "scit pune", "symbiosis centre for information technology"], "Pune", "Maharashtra"),
    _e("siu-pune", "Symbiosis International University", "Symbiosis Pune", ["siu", "symbiosis", "symbiosis international university", "symbiosis pune"], "Pune", "Maharashtra"),
    _e("bharatividyapeeth-pune", "Bharati Vidyapeeth College of Engineering", "BVCOE Pune", ["bvcoe", "bharati vidyapeeth", "bvcoe pune", "bharati vidyapeeth pune"], "Pune", "Maharashtra"),
    _e("pccoe-pune", "Pimpri Chinchwad College of Engineering", "PCCOE", ["pccoe", "pccoe pune", "pimpri chinchwad college of engineering"], "Pune", "Maharashtra"),
    _e("cummins-pune", "Cummins College of Engineering for Women", "Cummins Pune", ["cummins", "cummins pune", "mksss cummins"], "Pune", "Maharashtra"),
    _e("fergusson-pune", "Fergusson College", "Fergusson", ["fergusson", "fergusson college", "fc pune"], "Pune", "Maharashtra"),
    _e("sppu-pune", "Savitribai Phule Pune University", "SPPU", ["sppu", "pune university", "savitribai phule pune university", "unipune"], "Pune", "Maharashtra"),
    _e("aissms-pune", "AISSMS College of Engineering", "AISSMS", ["aissms", "aissms coe", "aissms pune"], "Pune", "Maharashtra"),
    _e("sinhgad-pune", "Sinhgad College of Engineering", "Sinhgad COE", ["sinhgad", "scoe pune", "sinhgad college of engineering vadgaon"], "Pune", "Maharashtra"),
    _e("dypatil-navimumbai", "D. Y. Patil College of Engineering, Navi Mumbai", "DY Patil Navi Mumbai", ["dy patil navi mumbai", "dypcoe navi mumbai", "d y patil nerul"], "Navi Mumbai", "Maharashtra"),
    _e("dypatil-pune", "Dr. D. Y. Patil Institute of Technology, Pimpri", "DY Patil Pune", ["dy patil pune", "dypit pimpri", "d y patil pimpri"], "Pune", "Maharashtra"),
    _e("terna-navimumbai", "Terna Engineering College", "Terna", ["terna", "terna nerul", "terna engineering college"], "Navi Mumbai", "Maharashtra"),
    _e("ycce-nagpur", "Yeshwantrao Chavan College of Engineering", "YCCE Nagpur", ["ycce", "ycce nagpur", "yeshwantrao chavan nagpur"], "Nagpur", "Maharashtra"),
    _e("rcoem-nagpur", "Shri Ramdeobaba College of Engineering and Management", "RCOEM", ["rcoem", "ramdeobaba", "rcoem nagpur", "shri ramdeobaba nagpur"], "Nagpur", "Maharashtra"),
    _e("ghrce-nagpur", "G.H. Raisoni College of Engineering Nagpur", "GHRCE", ["ghrce", "g h raisoni", "gh raisoni nagpur"], "Nagpur", "Maharashtra"),
    _e("pallotti-nagpur", "St. Vincent Pallotti College of Engineering and Technology", "Pallotti Nagpur", ["pallotti", "svpcet", "st vincent pallotti nagpur"], "Nagpur", "Maharashtra"),
    _e("walchand-sangli", "Walchand College of Engineering Sangli", "WCE Sangli", ["wce sangli", "walchand", "walchand college of engineering"], "Sangli", "Maharashtra"),
    _e("gcoa-amravati", "Government College of Engineering Amravati", "GCOEA", ["gcoea", "gcoe amravati", "government college of engineering amravati"], "Amravati", "Maharashtra"),
    _e("geca-aurangabad", "Government College of Engineering Aurangabad", "GECA", ["geca", "gec aurangabad", "government college of engineering aurangabad"], "Aurangabad", "Maharashtra"),
    _e("gcek-karad", "Government College of Engineering Karad", "GCEK", ["gcek", "gce karad", "government college of engineering karad"], "Karad", "Maharashtra"),
    _e("sggs-nanded", "Shri Guru Gobind Singhji Institute of Engineering and Technology", "SGGS Nanded", ["sggs", "sggs nanded", "sggie t nanded"], "Nanded", "Maharashtra"),
    _e("batu-lonere", "Dr. Babasaheb Ambedkar Technological University", "BATU Lonere", ["batu", "batu lonere", "dbatu", "dr babasaheb ambedkar technological university"], "Lonere", "Maharashtra"),
    # ---- Delhi NCR ----
    _e("dtu-delhi", "Delhi Technological University", "DTU", ["dtu", "dtu delhi", "delhi technological university", "delhi college of engineering", "dce"], "New Delhi", "Delhi"),
    _e("nsut-delhi", "Netaji Subhas University of Technology", "NSUT", ["nsut", "nsut delhi", "nsit", "netaji subhas university of technology", "netaji subhas institute of technology"], "New Delhi", "Delhi"),
    _e("igdtuw-delhi", "Indira Gandhi Delhi Technical University for Women", "IGDTUW", ["igdtuw", "igdtuw delhi", "igdtuw", "indira gandhi delhi technical university for women"], "New Delhi", "Delhi"),
    _e("jamia-delhi", "Jamia Millia Islamia (Faculty of Engineering)", "Jamia Millia Islamia", ["jamia", "jmi", "jamia millia islamia", "jmi delhi"], "New Delhi", "Delhi"),
    _e("hansraj-du", "Hansraj College, University of Delhi", "Hansraj College", ["hansraj", "hansraj college", "hans raj college du"], "New Delhi", "Delhi"),
    _e("hindu-du", "Hindu College, University of Delhi", "Hindu College", ["hindu college", "hindu college du"], "New Delhi", "Delhi"),
    _e("srcc-du", "Shri Ram College of Commerce, University of Delhi", "SRCC", ["srcc", "shri ram college of commerce"], "New Delhi", "Delhi"),
    _e("lsr-du", "Lady Shri Ram College, University of Delhi", "LSR", ["lsr", "lady shri ram college"], "New Delhi", "Delhi"),
    _e("miranda-du", "Miranda House, University of Delhi", "Miranda House", ["miranda house", "miranda house du"], "New Delhi", "Delhi"),
    _e("stephens-du", "St. Stephen's College, University of Delhi", "St. Stephen's", ["st stephens", "stephens college", "st stephen college du"], "New Delhi", "Delhi"),
    _e("kirorimal-du", "Kirori Mal College, University of Delhi", "Kirori Mal", ["kirori mal", "kmc du", "kirori mal college"], "New Delhi", "Delhi"),
    _e("ramjas-du", "Ramjas College, University of Delhi", "Ramjas", ["ramjas", "ramjas college"], "New Delhi", "Delhi"),
    _e("usict-delhi", "University School of Information, Communication and Technology (IPU)", "USICT Delhi", ["usict", "usict delhi", "ipu main campus", "ggsipu dwarka"], "New Delhi", "Delhi"),
    _e("mait-delhi", "Maharaja Agrasen Institute of Technology (IPU)", "MAIT Delhi", ["mait", "mait delhi", "maharaja agrasen institute of technology"], "New Delhi", "Delhi"),
    _e("bvp-delhi", "Bharati Vidyapeeth's College of Engineering, Delhi (IPU)", "BVP Delhi", ["bvp delhi", "bharati vidyapeeth delhi", "bvcoe delhi"], "New Delhi", "Delhi"),
    _e("msit-delhi", "Maharaja Surajmal Institute of Technology (IPU)", "MSIT Delhi", ["msit", "msit delhi", "maharaja surajmal institute of technology"], "New Delhi", "Delhi"),
    _e("gtbit-delhi", "Guru Tegh Bahadur Institute of Technology (IPU)", "GTBIT", ["gtbit", "gtbit delhi", "guru tegh bahadur institute of technology"], "New Delhi", "Delhi"),
    _e("jss-noida", "JSS Academy of Technical Education, Noida", "JSS Noida", ["jss noida", "jssate noida", "jss academy noida"], "Noida", "Uttar Pradesh"),
    _e("akgec-ghaziabad", "Ajay Kumar Garg Engineering College", "AKGEC", ["akgec", "ajay kumar garg", "akgec ghaziabad"], "Ghaziabad", "Uttar Pradesh"),
    _e("kiet-ghaziabad", "KIET Group of Institutions", "KIET Ghaziabad", ["kiet", "kiet ghaziabad", "krishna institute of engineering and technology"], "Ghaziabad", "Uttar Pradesh"),
    _e("abes-ghaziabad", "ABES Engineering College", "ABES Ghaziabad", ["abes", "abes ghaziabad", "abes engineering college"], "Ghaziabad", "Uttar Pradesh"),
    _e("gla-mathura", "GLA University", "GLA University", ["gla", "gla mathura", "gla university"], "Mathura", "Uttar Pradesh"),
    _e("sharda-noida", "Sharda University", "Sharda University", ["sharda", "sharda university", "sharda noida", "su noida"], "Greater Noida", "Uttar Pradesh"),
    _e("galgotias-noida", "Galgotias University", "Galgotias", ["galgotias", "galgotias university", "gu greater noida", "galgotias college"], "Greater Noida", "Uttar Pradesh"),
    _e("bennett-noida", "Bennett University", "Bennett University", ["bennett", "bennett university", "bu greater noida"], "Greater Noida", "Uttar Pradesh"),
    _e("snu-noida", "Shiv Nadar University, Noida", "Shiv Nadar Noida", ["snu noida", "snu dadri", "shiv nadar noida", "shiv nadar university"], "Dadri", "Uttar Pradesh"),
    _e("amity-noida", "Amity University, Noida", "Amity Noida", ["amity", "amity noida", "amity university", "amity university noida"], "Noida", "Uttar Pradesh"),
    _e("amity-mumbai", "Amity University, Mumbai", "Amity Mumbai", ["amity mumbai", "amity university mumbai"], "Mumbai", "Maharashtra"),
    _e("amity-jaipur", "Amity University, Jaipur", "Amity Jaipur", ["amity jaipur", "amity university jaipur"], "Jaipur", "Rajasthan"),
    _e("amity-kolkata", "Amity University, Kolkata", "Amity Kolkata", ["amity kolkata", "amity university kolkata"], "Kolkata", "West Bengal"),
    _e("amity-gurgaon", "Amity University, Gurgaon", "Amity Gurgaon", ["amity gurgaon", "amity haryana", "amity university gurgaon"], "Gurgaon", "Haryana"),
    _e("amity-lucknow", "Amity University, Lucknow", "Amity Lucknow", ["amity lucknow", "amity university lucknow"], "Lucknow", "Uttar Pradesh"),
    _e("amity-patna", "Amity University, Patna", "Amity Patna", ["amity patna", "amity university patna"], "Patna", "Bihar"),
    _e("amity-bangalore", "Amity University, Bengaluru", "Amity Bengaluru", ["amity bangalore", "amity bengaluru", "amity university bangalore"], "Bangalore", "Karnataka"),
    _e("ashoka-sonepat", "Ashoka University", "Ashoka University", ["ashoka", "ashoka university", "ashoka sonepat"], "Sonepat", "Haryana"),
    _e("jindal-sonepat", "O.P. Jindal Global University", "JGU Sonepat", ["jgu", "jindal", "op jindal", "o p jindal global university"], "Sonepat", "Haryana"),
    # ---- Telangana / Andhra Pradesh ----
    _e("jntuh-hyderabad", "Jawaharlal Nehru Technological University Hyderabad", "JNTUH", ["jntuh", "jntu hyderabad", "jnt hyderabad", "jawaharlal nehru technological university hyderabad"], "Hyderabad", "Telangana"),
    _e("jntuk-kakinada", "Jawaharlal Nehru Technological University Kakinada", "JNTUK", ["jntuk", "jntu kakinada", "jnt kakinada", "jawaharlal nehru technological university kakinada"], "Kakinada", "Andhra Pradesh"),
    _e("jntua-anantapur", "Jawaharlal Nehru Technological University Anantapur", "JNTUA", ["jntua", "jntu anantapur", "jawaharlal nehru technological university anantapur"], "Anantapur", "Andhra Pradesh"),
    _e("ou-hyderabad", "Osmania University (University College of Engineering)", "OU Hyderabad", ["ou hyderabad", "osmania", "osmania university", "uce ou"], "Hyderabad", "Telangana"),
    _e("cbit-hyderabad", "Chaitanya Bharathi Institute of Technology", "CBIT Hyderabad", ["cbit", "cbit hyderabad", "chaitanya bharathi"], "Hyderabad", "Telangana"),
    _e("vasavi-hyderabad", "Vasavi College of Engineering", "Vasavi", ["vasavi", "vasavi hyderabad", "vasavi college of engineering"], "Hyderabad", "Telangana"),
    _e("vnr-hyderabad", "VNR Vignana Jyothi Institute of Engineering and Technology", "VNR VJIET", ["vnr", "vnr vjiet", "vnr vignana jyothi"], "Hyderabad", "Telangana"),
    _e("griet-hyderabad", "Gokaraju Rangaraju Institute of Engineering and Technology", "GRIET", ["griet", "griet hyderabad", "gokaraju rangaraju"], "Hyderabad", "Telangana"),
    _e("mgit-hyderabad", "Mahatma Gandhi Institute of Technology", "MGIT", ["mgit", "mgit hyderabad", "mahatma gandhi institute of technology gandipet"], "Hyderabad", "Telangana"),
    _e("anurag-hyderabad", "Anurag University", "Anurag University", ["anurag", "anurag university", "anurag hyderabad", "cvsr"], "Hyderabad", "Telangana"),
    _e("cmr-hyderabad", "CMR Institute of Technology, Hyderabad", "CMR Hyderabad", ["cmr hyderabad", "cmr institute of technology hyderabad"], "Hyderabad", "Telangana"),
    _e("mlrit-hyderabad", "MLR Institute of Technology", "MLRIT", ["mlrit", "mlr institute of technology", "mlrit hyderabad"], "Hyderabad", "Telangana"),
    _e("icfai-hyderabad", "ICFAI Foundation for Higher Education (IFHE)", "IFHE Hyderabad", ["ifhe", "icfai hyderabad", "icfai tech", "ifhe hyderabad"], "Hyderabad", "Telangana"),
    _e("mahindra-hyderabad", "Mahindra University", "Mahindra University", ["mahindra", "mahindra university", "mu hyderabad", "mahindra ecole"], "Hyderabad", "Telangana"),
    _e("woxsen-hyderabad", "Woxsen University", "Woxsen", ["woxsen", "woxsen university"], "Hyderabad", "Telangana"),
    _e("au-visakhapatnam", "Andhra University College of Engineering", "AUCE Vizag", ["auce", "andhra university", "au visakhapatnam", "aucoe"], "Visakhapatnam", "Andhra Pradesh"),
    _e("svu-tirupati", "Sri Venkateswara University College of Engineering", "SVUCE Tirupati", ["svuce", "svu tirupati", "sri venkateswara university"], "Tirupati", "Andhra Pradesh"),
    _e("kl-guntur", "Koneru Lakshmaiah Education Foundation (KL University)", "KL University", ["klu", "kl university", "koneru lakshmaiah", "kl guntur", "kl vijayawada"], "Guntur", "Andhra Pradesh"),
    _e("vignan-guntur", "Vignan's Foundation for Science, Technology and Research", "VFSTR", ["vfstr", "vignan", "vignan guntur", "vignan university"], "Guntur", "Andhra Pradesh"),
    _e("srkr-bhimavaram", "Sagi Rama Krishnam Raju Engineering College", "SRKR", ["srkr", "srkr bhimavaram"], "Bhimavaram", "Andhra Pradesh"),
    _e("gvp-visakhapatnam", "Gayatri Vidya Parishad College of Engineering", "GVP Vizag", ["gvp", "gvp visakhapatnam", "gayatri vidya parishad"], "Visakhapatnam", "Andhra Pradesh"),
    _e("anits-visakhapatnam", "Anil Neerukonda Institute of Technology and Sciences", "ANITS Vizag", ["anits", "anits visakhapatnam", "anil neerukonda"], "Visakhapatnam", "Andhra Pradesh"),
    # ---- Kerala ----
    _e("cusat-kochi", "Cochin University of Science and Technology", "CUSAT", ["cusat", "cusat kochi", "cochin university of science and technology", "soet cusat"], "Kochi", "Kerala"),
    _e("cet-trivandrum", "College of Engineering Trivandrum", "CET Trivandrum", ["cet", "cet trivandrum", "cet thiruvananthapuram", "college of engineering trivandrum"], "Thiruvananthapuram", "Kerala"),
    _e("gec-thrissur", "Government Engineering College Thrissur", "GEC Thrissur", ["gec thrissur", "government engineering college thrissur"], "Thrissur", "Kerala"),
    _e("gce-kannur", "Government College of Engineering Kannur", "GCE Kannur", ["gce kannur", "government college of engineering kannur"], "Kannur", "Kerala"),
    _e("mec-kochi", "Model Engineering College, Kochi", "MEC Kochi", ["mec", "mec kochi", "model engineering college", "mec thrikkakara"], "Kochi", "Kerala"),
    _e("rit-kottayam", "Rajiv Gandhi Institute of Technology Kottayam", "RIT Kottayam", ["rit kottayam", "rajiv gandhi institute of technology kottayam"], "Kottayam", "Kerala"),
    _e("tkm-kollam", "TKM College of Engineering", "TKM Kollam", ["tkm", "tkm kollam", "tkm college of engineering"], "Kollam", "Kerala"),
    # ---- Gujarat ----
    _e("daiict-gandhinagar", "Dhirubhai Ambani Institute of Information and Communication Technology", "DA-IICT", ["daiict", "da-iict", "daiict gandhinagar", "dhirubhai ambani institute"], "Gandhinagar", "Gujarat"),
    _e("nirma-ahmedabad", "Nirma University (Institute of Technology)", "Nirma", ["nirma", "nirma university", "itnu", "nirma ahmedabad"], "Ahmedabad", "Gujarat"),
    _e("pdeu-gandhinagar", "Pandit Deendayal Energy University", "PDEU", ["pdeu", "pdpu", "pandit deendayal energy university", "pdpu gandhinagar"], "Gandhinagar", "Gujarat"),
    _e("msu-baroda", "Maharaja Sayajirao University (Faculty of Technology)", "MSU Baroda", ["msu baroda", "msu vadodara", "maharaja sayajirao university", "fte msu"], "Vadodara", "Gujarat"),
    _e("ldce-ahmedabad", "L.D. College of Engineering", "LDCE", ["ldce", "ld college of engineering", "ldce ahmedabad"], "Ahmedabad", "Gujarat"),
    _e("vgec-ahmedabad", "Vishwakarma Government Engineering College", "VGEC", ["vgec", "vgec ahmedabad", "vishwakarma government engineering college"], "Ahmedabad", "Gujarat"),
    _e("ddu-nadiad", "Dharmsinh Desai University", "DDU Nadiad", ["ddu", "ddu nadiad", "dharmsinh desai university"], "Nadiad", "Gujarat"),
    _e("charusat-anand", "Charotar University of Science and Technology", "CHARUSAT", ["charusat", "charusat anand", "charotar university"], "Anand", "Gujarat"),
    _e("marwadi-rajkot", "Marwadi University", "Marwadi University", ["marwadi", "marwadi university", "marwadi rajkot", "mu rajkot"], "Rajkot", "Gujarat"),
    _e("rku-rajkot", "RK University", "RK University", ["rku", "rk university", "rk university rajkot"], "Rajkot", "Gujarat"),
    # ---- Rajasthan ----
    _e("skit-jaipur", "Swami Keshvanand Institute of Technology", "SKIT Jaipur", ["skit", "skit jaipur", "swami keshvanand"], "Jaipur", "Rajasthan"),
    _e("jecrc-jaipur", "Jaipur Engineering College and Research Centre", "JECRC", ["jecrc", "jecrc jaipur"], "Jaipur", "Rajasthan"),
    _e("poornima-jaipur", "Poornima College of Engineering", "Poornima", ["poornima", "poornima jaipur", "pce jaipur"], "Jaipur", "Rajasthan"),
    _e("lnmiit-jaipur", "LNM Institute of Information Technology", "LNMIIT", ["lnmiit", "lnm iit", "lnm institute of information technology", "lnmiit jaipur"], "Jaipur", "Rajasthan"),
    _e("mbm-jodhpur", "MBM University (M.B.M. Engineering College)", "MBM Jodhpur", ["mbm", "mbm jodhpur", "mbm engineering college", "mbm university"], "Jodhpur", "Rajasthan"),
    _e("ctae-udaipur", "College of Technology and Engineering, Udaipur", "CTAE Udaipur", ["ctae", "ctae udaipur", "mpuat udaipur"], "Udaipur", "Rajasthan"),
    _e("rtu-kota", "Rajasthan Technical University", "RTU Kota", ["rtu", "rtu kota", "rajasthan technical university", "uit rtu"], "Kota", "Rajasthan"),
    # ---- Madhya Pradesh ----
    _e("sgsits-indore", "Shri Govindram Seksaria Institute of Technology and Science", "SGSITS Indore", ["sgsits", "sgsits indore", "seksaria indore"], "Indore", "Madhya Pradesh"),
    _e("ietdavv-indore", "Institute of Engineering and Technology, DAVV", "IET DAVV", ["iet davv", "iet-davv indore", "davv indore"], "Indore", "Madhya Pradesh"),
    _e("mits-gwalior", "Madhav Institute of Technology and Science", "MITS Gwalior", ["mits gwalior", "mits", "madhav institute of technology"], "Gwalior", "Madhya Pradesh"),
    _e("sati-vidisha", "Samrat Ashok Technological Institute", "SATI Vidisha", ["sati", "sati vidisha", "samrat ashok technological institute"], "Vidisha", "Madhya Pradesh"),
    _e("jec-jabalpur", "Jabalpur Engineering College", "JEC Jabalpur", ["jec jabalpur", "jec", "jabalpur engineering college"], "Jabalpur", "Madhya Pradesh"),
    _e("lnct-bhopal", "Lakshmi Narain College of Technology", "LNCT Bhopal", ["lnct", "lnct bhopal", "lakshmi narain college"], "Bhopal", "Madhya Pradesh"),
    _e("oriental-bhopal", "Oriental Institute of Science and Technology", "Oriental Bhopal", ["oriental bhopal", "oist bhopal"], "Bhopal", "Madhya Pradesh"),
    _e("medicaps-indore", "Medi-Caps University", "Medi-Caps", ["medicaps", "medi-caps university", "medicaps indore", "mu indore"], "Indore", "Madhya Pradesh"),
    _e("svvv-indore", "Shri Vaishnav Vidyapeeth Vishwavidyalaya", "SVVV Indore", ["svvv", "svvv indore", "shri vaishnav vidyapeeth"], "Indore", "Madhya Pradesh"),
    # ---- Uttar Pradesh (beyond NCR) ----
    _e("hbtu-kanpur", "Harcourt Butler Technical University", "HBTU Kanpur", ["hbtu", "hbtu kanpur", "harcourt butler technical university", "hbt kanpur"], "Kanpur", "Uttar Pradesh"),
    _e("iet-lucknow", "Institute of Engineering and Technology, Lucknow", "IET Lucknow", ["iet lucknow", "iet lucknow aktu"], "Lucknow", "Uttar Pradesh"),
    _e("mmmut-gorakhpur", "Madan Mohan Malaviya University of Technology", "MMMUT", ["mmmut", "mmmut gorakhpur", "mmmec", "madan mohan malaviya"], "Gorakhpur", "Uttar Pradesh"),
    _e("knit-sultanpur", "Kamla Nehru Institute of Technology", "KNIT Sultanpur", ["knit", "knit sultanpur", "kamla nehru institute"], "Sultanpur", "Uttar Pradesh"),
    _e("biet-jhansi", "Bundelkhand Institute of Engineering and Technology", "BIET Jhansi", ["biet jhansi", "biet", "bundelkhand institute"], "Jhansi", "Uttar Pradesh"),
    _e("amu-aligarh", "Aligarh Muslim University (ZHCET)", "AMU Aligarh", ["amu", "amu aligarh", "aligarh muslim university", "zhcet"], "Aligarh", "Uttar Pradesh"),
    # ---- Bihar / Jharkhand / Odisha / Chhattisgarh ----
    _e("bit-sindri", "BIT Sindri", "BIT Sindri", ["bit sindri", "bit sindri dhanbad"], "Dhanbad", "Jharkhand"),
    _e("mit-muzaffarpur", "Muzaffarpur Institute of Technology", "MIT Muzaffarpur", ["mit muzaffarpur", "muzaffarpur institute of technology"], "Muzaffarpur", "Bihar"),
    _e("bce-bhagalpur", "Bhagalpur College of Engineering", "BCE Bhagalpur", ["bce bhagalpur", "bhagalpur college of engineering"], "Bhagalpur", "Bihar"),
    _e("vssut-burla", "Veer Surendra Sai University of Technology", "VSSUT Burla", ["vssut", "vssut burla", "uce burla", "veer surendra sai"], "Burla", "Odisha"),
    _e("outr-bhubaneswar", "Odisha University of Technology and Research", "OUTR Bhubaneswar", ["outr", "cet bhubaneswar", "cet bbsr", "college of engineering and technology bhubaneswar"], "Bhubaneswar", "Odisha"),
    _e("kiit-bhubaneswar", "Kalinga Institute of Industrial Technology", "KIIT", ["kiit", "kiit bhubaneswar", "kalinga institute of industrial technology", "kiit university"], "Bhubaneswar", "Odisha"),
    _e("soa-bhubaneswar", "Siksha 'O' Anusandhan (ITER)", "SOA / ITER", ["soa", "iter", "soa bhubaneswar", "iter bhubaneswar", "siksha o anusandhan"], "Bhubaneswar", "Odisha"),
    _e("cvrce-bhubaneswar", "C.V. Raman Global University", "CV Raman", ["cv raman", "cvrce", "c v raman global university", "cgu odisha"], "Bhubaneswar", "Odisha"),
    _e("silicon-bhubaneswar", "Silicon Institute of Technology", "Silicon BBSR", ["silicon", "silicon bhubaneswar", "silicon institute of technology"], "Bhubaneswar", "Odisha"),
    _e("nist-berhampur", "NIST Institute of Science and Technology", "NIST Berhampur", ["nist", "nist berhampur", "national institute of science and technology"], "Berhampur", "Odisha"),
    _e("gec-raipur", "Government Engineering College Raipur", "GEC Raipur", ["gec raipur", "government engineering college raipur"], "Raipur", "Chhattisgarh"),
    _e("gec-bilaspur", "Government Engineering College Bilaspur", "GEC Bilaspur", ["gec bilaspur", "government engineering college bilaspur"], "Bilaspur", "Chhattisgarh"),
    _e("bit-durg", "Bhilai Institute of Technology, Durg", "BIT Durg", ["bit durg", "bit durg bhilai", "bhilai institute of technology"], "Durg", "Chhattisgarh"),
    _e("rungta-bhilai", "Rungta College of Engineering and Technology", "Rungta Bhilai", ["rungta", "rungta bhilai", "rcet bhilai"], "Bhilai", "Chhattisgarh"),
    # ---- Punjab / Haryana / HP / J&K ----
    _e("pec-chandigarh", "Punjab Engineering College, Chandigarh", "PEC Chandigarh", ["pec", "pec chandigarh", "punjab engineering college"], "Chandigarh", "Chandigarh"),
    _e("uiet-chandigarh", "University Institute of Engineering and Technology, Panjab University", "UIET Chandigarh", ["uiet", "uiet chandigarh", "uiet pu"], "Chandigarh", "Chandigarh"),
    _e("gndu-amritsar", "Guru Nanak Dev University (Engineering)", "GNDU Amritsar", ["gndu", "gndu amritsar", "guru nanak dev university"], "Amritsar", "Punjab"),
    _e("lpu-phagwara", "Lovely Professional University", "LPU", ["lpu", "lovely professional university", "lpu phagwara", "lpu jalandhar"], "Phagwara", "Punjab"),
    _e("cu-mohali", "Chandigarh University", "Chandigarh University", ["cu", "chandigarh university", "cu mohali", "cu gharuan"], "Mohali", "Punjab"),
    _e("chitkara-patiala", "Chitkara University, Punjab", "Chitkara Punjab", ["chitkara", "chitkara patiala", "chitkara university punjab"], "Patiala", "Punjab"),
    _e("chitkara-baddi", "Chitkara University, Himachal Pradesh", "Chitkara Baddi", ["chitkara baddi", "chitkara himachal", "chitkara university baddi"], "Baddi", "Himachal Pradesh"),
    _e("ymca-faridabad", "J.C. Bose University of Science and Technology (YMCA)", "YMCA Faridabad", ["ymca", "ymca faridabad", "jc bose university", "ymcaust"], "Faridabad", "Haryana"),
    _e("dcrust-murthal", "Deenbandhu Chhotu Ram University of Science and Technology", "DCRUST Murthal", ["dcrust", "dcrust murthal", "deenbandhu chhotu ram"], "Murthal", "Haryana"),
    _e("gju-hisar", "Guru Jambheshwar University of Science and Technology", "GJUST Hisar", ["gju", "gjust", "gju hisar", "guru jambheshwar"], "Hisar", "Haryana"),
    _e("mdu-rohtak", "Maharshi Dayanand University (UIET)", "MDU Rohtak", ["mdu", "mdu rohtak", "maharshi dayanand university"], "Rohtak", "Haryana"),
    _e("gcet-jammu", "Government College of Engineering and Technology Jammu", "GCET Jammu", ["gcet jammu", "gcet", "government college of engineering jammu"], "Jammu", "Jammu and Kashmir"),
    _e("miet-jammu", "Model Institute of Engineering and Technology", "MIET Jammu", ["miet jammu", "miet", "model institute of engineering and technology"], "Jammu", "Jammu and Kashmir"),
    _e("ssm-srinagar", "SSM College of Engineering", "SSM Srinagar", ["ssm", "ssm srinagar", "ssm college of engineering"], "Srinagar", "Jammu and Kashmir"),
    # ---- Northeast ----
    _e("aec-guwahati", "Assam Engineering College", "AEC Guwahati", ["aec", "aec guwahati", "assam engineering college"], "Guwahati", "Assam"),
    _e("jec-jorhat", "Jorhat Engineering College", "JEC Jorhat", ["jec jorhat", "jec", "jorhat engineering college"], "Jorhat", "Assam"),
    _e("nerist-itanagar", "North Eastern Regional Institute of Science and Technology", "NERIST", ["nerist", "nerist itanagar"], "Itanagar", "Arunachal Pradesh"),
    # ---- Uttarakhand / Goa ----
    _e("gbpuat-pantnagar", "G.B. Pant University of Agriculture and Technology (COT)", "GBPUAT Pantnagar", ["gbpuat", "pantnagar", "g b pant university", "cot pantnagar"], "Pantnagar", "Uttarakhand"),
    _e("dit-dehradun", "DIT University", "DIT Dehradun", ["dit", "dit dehradun", "dit university", "dit dehradun"], "Dehradun", "Uttarakhand"),
    _e("geu-dehradun", "Graphic Era University", "Graphic Era", ["geu", "graphic era", "graphic era dehradun", "geu dehradun"], "Dehradun", "Uttarakhand"),
    _e("upes-dehradun", "University of Petroleum and Energy Studies", "UPES", ["upes", "upes dehradun", "university of petroleum and energy studies"], "Dehradun", "Uttarakhand"),
    _e("thdc-tehri", "THDC Institute of Hydropower Engineering and Technology", "THDC Tehri", ["thdc", "thdc tehri"], "Tehri", "Uttarakhand"),
    _e("gec-farmagudi", "Goa College of Engineering", "GEC Goa", ["gec goa", "gec farmagudi", "goa college of engineering", "gec farmagudi"], "Ponda", "Goa"),
    _e("pcce-verna", "Padre Conceicao College of Engineering", "PCCE Verna", ["pcce", "pcce verna", "padre conceicao", "pcce goa"], "Verna", "Goa"),
    # ---- West Bengal (rest) ----
    _e("jadavpur-kolkata", "Jadavpur University (Faculty of Engineering)", "Jadavpur University", ["jadavpur", "ju kolkata", "jadavpur university"], "Kolkata", "West Bengal"),
    _e("kgec-nadia", "Kalyani Government Engineering College", "KGEC", ["kgec", "kgec nadia", "kalyani government engineering college"], "Nadia", "West Bengal"),
    _e("jgec-jalpaiguri", "Jalpaiguri Government Engineering College", "JGEC", ["jgec", "jgec jalpaiguri", "jalpaiguri government engineering college"], "Jalpaiguri", "West Bengal"),
    _e("heritage-kolkata", "Heritage Institute of Technology", "Heritage Kolkata", ["heritage", "hit kolkata", "heritage institute of technology"], "Kolkata", "West Bengal"),
    _e("techno-saltlake", "Techno Main Salt Lake", "Techno Salt Lake", ["techno salt lake", "techno main salt lake", "techno india salt lake", "tmsl"], "Kolkata", "West Bengal"),
    _e("iem-kolkata", "Institute of Engineering and Management", "IEM Kolkata", ["iem", "iem kolkata", "institute of engineering and management"], "Kolkata", "West Bengal"),
    _e("xaviers-kolkata", "St. Xavier's College Kolkata", "St. Xavier's Kolkata", ["xaviers kolkata", "st xaviers kolkata"], "Kolkata", "West Bengal"),
    _e("presidency-kolkata", "Presidency University Kolkata", "Presidency Kolkata", ["presidency kolkata", "presidency university kolkata"], "Kolkata", "West Bengal"),
    _e("cu-kolkata", "University of Calcutta (UCSTA)", "Calcutta University", ["calcutta university", "ucsta", "university of calcutta"], "Kolkata", "West Bengal"),
]


_ALIAS_INDEX: dict[str, dict] = {}
_ID_INDEX: dict[str, dict] = {}
for _entry in COLLEGES:
    _ID_INDEX[_entry["id"]] = _entry
    keys = {_norm(_entry["name"]), _norm(_entry["short"])}
    keys.update(_norm(a) for a in _entry["aliases"])
    for _key in keys:
        if _key:
            _ALIAS_INDEX.setdefault(_key, _entry)


def get_college(college_id: str | None) -> dict | None:
    """Fetch a directory entry by id."""
    if not college_id:
        return None
    return _ID_INDEX.get(college_id)


def resolve_college(text: str | None) -> dict | None:
    """Resolve free text ("VIT", "Vellore Institute of Technology") to an entry."""
    key = _norm(text)
    if not key:
        return None
    entry = _ALIAS_INDEX.get(key)
    if entry is not None:
        return entry
    # Token-set equality catches reorderings like "Bombay IIT".
    tokens = sorted(key.split())
    if len(tokens) >= 2:
        for alias, candidate in _ALIAS_INDEX.items():
            if sorted(alias.split()) == tokens:
                return candidate
    return None


def canonical_college_id(text: str | None) -> str | None:
    """Stable comparison key.

    Directory hits use the entry id; anything else falls into the ``custom:``
    namespace so identical custom text still matches.
    """
    key = _norm(text)
    if not key:
        return None
    entry = resolve_college(text)
    if entry is not None:
        return entry["id"]
    return f"custom:{key}"


def same_college(a: str | None, a_id: str | None, b: str | None, b_id: str | None) -> bool:
    """Whether two (text, id) college references mean the same institution."""
    if a_id and b_id:
        return a_id == b_id
    a_key = a_id or canonical_college_id(a)
    b_key = b_id or canonical_college_id(b)
    return bool(a_key and b_key and a_key == b_key)


def resolve_input(
    college_id: str | None, college_text: str | None
) -> tuple[str | None, str | None]:
    """Normalize a (college_id, free-text) pair from API input.

    Returns (id, display_name). Raises ValueError for unknown ids.
    Free text that matches the directory upgrades to the canonical entry;
    anything else stays as custom text with a NULL id.
    """
    cleaned_id = (college_id or "").strip() or None
    cleaned_text = (college_text or "").strip() or None
    if cleaned_id is not None:
        entry = get_college(cleaned_id)
        if entry is None:
            raise ValueError(f"Unknown college_id '{cleaned_id}'")
        return entry["id"], entry["name"]
    if cleaned_text is None:
        return None, None
    entry = resolve_college(cleaned_text)
    if entry is not None:
        return entry["id"], entry["name"]
    return None, cleaned_text


def search_colleges(query: str, limit: int = 8) -> list[dict]:
    """Ranked substring/prefix search for comboboxes."""
    key = _norm(query)
    if not key or len(key) < 2:
        return []
    ranked: list[tuple[int, dict]] = []
    for entry in COLLEGES:
        candidates = [_norm(entry["name"]), _norm(entry["short"])]
        candidates.extend(_norm(a) for a in entry["aliases"])
        candidates.append(_norm(f"{entry['city']} {entry['state']}"))
        best = None
        for cand in candidates:
            if not cand:
                continue
            if cand == key:
                rank = -1
            elif cand.startswith(key + " ") or key == cand:
                rank = 0
            elif any(w.startswith(key) for w in cand.split()):
                rank = 1
            elif key in cand:
                rank = 2
            else:
                continue
            best = rank if best is None else min(best, rank)
            if best == -1:
                break
        if best is not None:
            ranked.append((best, entry))
    ranked.sort(key=lambda item: (item[0], item[1]["name"]))
    return [entry for _, entry in ranked[:limit]]
