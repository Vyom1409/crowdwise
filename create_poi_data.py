import json
import os

poi_db = {
    "metros": [
        # Yellow Line
        {"name": "Samaypur Badli Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.7458, "lon": 77.1353, "interchange": False},
        {"name": "Azadpur Metro", "line": "Yellow / Pink Line", "color": "#facc15", "lat": 28.7072, "lon": 77.1802, "interchange": True},
        {"name": "GTB Nagar Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.6978, "lon": 77.2069, "interchange": False},
        {"name": "Vishwavidyalaya Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.6952, "lon": 77.2141, "interchange": False},
        {"name": "Kashmere Gate Metro", "line": "Red / Yellow / Violet Line", "color": "#facc15", "lat": 28.6675, "lon": 77.2285, "interchange": True},
        {"name": "Chandni Chowk Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.6578, "lon": 77.2302, "interchange": False},
        {"name": "New Delhi Metro", "line": "Yellow / Airport Line", "color": "#facc15", "lat": 28.6431, "lon": 77.2224, "interchange": True},
        {"name": "Rajiv Chowk Metro (Connaught Place)", "line": "Yellow / Blue Line", "color": "#3b82f6", "lat": 28.6328, "lon": 77.2195, "interchange": True},
        {"name": "Patel Chowk Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.6231, "lon": 77.2138, "interchange": False},
        {"name": "Central Secretariat Metro", "line": "Yellow / Violet Line", "color": "#8b5cf6", "lat": 28.6147, "lon": 77.2119, "interchange": True},
        {"name": "Udyog Bhawan Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.6108, "lon": 77.2122, "interchange": False},
        {"name": "Lok Kalyan Marg Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.5992, "lon": 77.2104, "interchange": False},
        {"name": "Jor Bagh Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.5878, "lon": 77.2116, "interchange": False},
        {"name": "Dilli Haat - INA Metro", "line": "Yellow / Pink Line", "color": "#facc15", "lat": 28.5752, "lon": 77.2085, "interchange": True},
        {"name": "AIIMS Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.5672, "lon": 77.2100, "interchange": False},
        {"name": "Green Park Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.5588, "lon": 77.2065, "interchange": False},
        {"name": "Hauz Khas Metro", "line": "Yellow / Magenta Line", "color": "#d946ef", "lat": 28.5432, "lon": 77.2064, "interchange": True},
        {"name": "Malviya Nagar Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.5284, "lon": 77.2061, "interchange": False},
        {"name": "Saket Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.5204, "lon": 77.2016, "interchange": False},
        {"name": "Qutab Minar Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.5129, "lon": 77.1862, "interchange": False},
        {"name": "Chhatarpur Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.5031, "lon": 77.1751, "interchange": False},
        {"name": "Sultanpur Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.4988, "lon": 77.1616, "interchange": False},
        {"name": "Ghitorni Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.4939, "lon": 77.1492, "interchange": False},
        {"name": "Arjan Garh Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.4809, "lon": 77.1259, "interchange": False},
        {"name": "Guru Dronacharya Metro", "line": "Yellow Line", "color": "#facc15", "lat": 28.4819, "lon": 77.1025, "interchange": False},
        {"name": "Sikanderpur Metro", "line": "Yellow / Rapid Metro", "color": "#facc15", "lat": 28.4816, "lon": 77.0929, "interchange": True},

        # Violet Line
        {"name": "Delhi Gate Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.6415, "lon": 77.2407, "interchange": False},
        {"name": "ITO Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.6299, "lon": 77.2403, "interchange": False},
        {"name": "Mandi House Metro", "line": "Blue / Violet Line", "color": "#3b82f6", "lat": 28.6258, "lon": 77.2341, "interchange": True},
        {"name": "Janpath Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.6206, "lon": 77.2185, "interchange": False},
        {"name": "Khan Market Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.6010, "lon": 77.2275, "interchange": False},
        {"name": "Jawaharlal Nehru Stadium Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5902, "lon": 77.2345, "interchange": False},
        {"name": "Jangpura Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5831, "lon": 77.2372, "interchange": False},
        {"name": "Lajpat Nagar Metro", "line": "Violet / Pink Line", "color": "#ec4899", "lat": 28.5708, "lon": 77.2373, "interchange": True},
        {"name": "Moolchand Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5658, "lon": 77.2343, "interchange": False},
        {"name": "Kailash Colony Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5552, "lon": 77.2422, "interchange": False},
        {"name": "Nehru Place Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5494, "lon": 77.2528, "interchange": False},
        {"name": "Kalkaji Mandir Metro", "line": "Violet / Magenta Line", "color": "#d946ef", "lat": 28.5498, "lon": 77.2598, "interchange": True},
        {"name": "Govind Puri Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5369, "lon": 77.2644, "interchange": False},
        {"name": "Harkesh Nagar Okhla Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5332, "lon": 77.2762, "interchange": False},
        {"name": "Jasola Apollo Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5393, "lon": 77.2842, "interchange": False},
        {"name": "Sarita Vihar Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5284, "lon": 77.2954, "interchange": False},
        {"name": "Mohan Estate Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5192, "lon": 77.2995, "interchange": False},
        {"name": "Tughlakabad Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.5115, "lon": 77.3015, "interchange": False},
        {"name": "Badarpur Border Metro", "line": "Violet Line", "color": "#8b5cf6", "lat": 28.4975, "lon": 77.3025, "interchange": False},

        # Blue Line
        {"name": "Dwarka Sector 21 Metro", "line": "Blue / Airport Line", "color": "#3b82f6", "lat": 28.5522, "lon": 77.0583, "interchange": True},
        {"name": "Dwarka Mor Metro", "line": "Blue Line", "color": "#3b82f6", "lat": 28.6192, "lon": 77.0331, "interchange": False},
        {"name": "Uttam Nagar East Metro", "line": "Blue Line", "color": "#3b82f6", "lat": 28.6214, "lon": 77.0601, "interchange": False},
        {"name": "Janakpuri West Metro", "line": "Blue / Magenta Line", "color": "#3b82f6", "lat": 28.6293, "lon": 77.0775, "interchange": True},
        {"name": "Tilak Nagar Metro", "line": "Blue Line", "color": "#3b82f6", "lat": 28.6366, "lon": 77.0964, "interchange": False},
        {"name": "Rajouri Garden Metro", "line": "Blue / Pink Line", "color": "#3b82f6", "lat": 28.6485, "lon": 77.1218, "interchange": True},
        {"name": "Kirti Nagar Metro", "line": "Blue / Green Line", "color": "#3b82f6", "lat": 28.6558, "lon": 77.1518, "interchange": True},
        {"name": "Patel Nagar Metro", "line": "Blue Line", "color": "#3b82f6", "lat": 28.6542, "lon": 77.1652, "interchange": False},
        {"name": "Rajendra Place Metro", "line": "Blue Line", "color": "#3b82f6", "lat": 28.6425, "lon": 77.1782, "interchange": False},
        {"name": "Karol Bagh Metro", "line": "Blue Line", "color": "#3b82f6", "lat": 28.6441, "lon": 77.1904, "interchange": False},
        {"name": "Akshardham Metro", "line": "Blue Line", "color": "#3b82f6", "lat": 28.6180, "lon": 77.2790, "interchange": False},
        {"name": "Mayur Vihar-1 Metro", "line": "Blue / Pink Line", "color": "#3b82f6", "lat": 28.6042, "lon": 77.2915, "interchange": True},
        {"name": "Noida Sector 18 Metro (Atta Market)", "line": "Blue Line", "color": "#3b82f6", "lat": 28.5708, "lon": 77.3255, "interchange": False},
        {"name": "Botanical Garden Metro", "line": "Blue / Magenta Line", "color": "#3b82f6", "lat": 28.5642, "lon": 77.3342, "interchange": True},
        {"name": "Anand Vihar ISBT Metro", "line": "Blue / Pink Line", "color": "#3b82f6", "lat": 28.6469, "lon": 77.3160, "interchange": True},

        # Magenta & Pink & Airport Line
        {"name": "Dhaula Kuan Metro (Airport Express)", "line": "Airport Express Line", "color": "#f97316", "lat": 28.5921, "lon": 77.1617, "interchange": True},
        {"name": "South Campus Metro (Dhaula Kuan)", "line": "Pink Line", "color": "#ec4899", "lat": 28.5878, "lon": 77.1652, "interchange": False},
        {"name": "Munirka Metro", "line": "Magenta Line", "color": "#d946ef", "lat": 28.5583, "lon": 77.1738, "interchange": False},
        {"name": "RK Puram Metro", "line": "Magenta Line", "color": "#d946ef", "lat": 28.5518, "lon": 77.1852, "interchange": False},
        {"name": "IIT Delhi Metro", "line": "Magenta Line", "color": "#d946ef", "lat": 28.5445, "lon": 77.1955, "interchange": False},
        {"name": "Chirag Delhi Metro", "line": "Magenta Line", "color": "#d946ef", "lat": 28.5398, "lon": 77.2285, "interchange": False},
        {"name": "Greater Kailash Metro", "line": "Magenta Line", "color": "#d946ef", "lat": 28.5422, "lon": 77.2412, "interchange": False},
        {"name": "Nehru Enclave Metro", "line": "Magenta Line", "color": "#d946ef", "lat": 28.5468, "lon": 77.2515, "interchange": False},
        {"name": "South Extension Metro", "line": "Pink Line", "color": "#ec4899", "lat": 28.5701, "lon": 77.2219, "interchange": False},
        {"name": "Sarai Kale Khan - Nizamuddin Metro", "line": "Pink Line", "color": "#ec4899", "lat": 28.5888, "lon": 77.2547, "interchange": False},
        {"name": "Ashram Metro", "line": "Pink Line", "color": "#ec4899", "lat": 28.5787, "lon": 77.2592, "interchange": False},
        {"name": "Shahdara Metro", "line": "Red Line", "color": "#ef4444", "lat": 28.6734, "lon": 77.2917, "interchange": False},
        {"name": "Netaji Subhash Place Metro", "line": "Red / Pink Line", "color": "#ef4444", "lat": 28.6965, "lon": 77.1528, "interchange": True},
        {"name": "Pitampura Metro", "line": "Red Line", "color": "#ef4444", "lat": 28.6990, "lon": 77.1384, "interchange": False},
        {"name": "Rohini West Metro", "line": "Red Line", "color": "#ef4444", "lat": 28.7150, "lon": 77.1140, "interchange": False},
        {"name": "Rithala Metro", "line": "Red Line", "color": "#ef4444", "lat": 28.7205, "lon": 77.1070, "interchange": False},
        {"name": "Inderlok Metro", "line": "Red / Green Line", "color": "#ef4444", "lat": 28.6732, "lon": 77.1698, "interchange": True},
        {"name": "Punjabi Bagh West Metro", "line": "Pink / Green Line", "color": "#ec4899", "lat": 28.6688, "lon": 77.1327, "interchange": True},
        {"name": "Delhi Aerocity Metro", "line": "Airport Express Line", "color": "#f97316", "lat": 28.5488, "lon": 77.1215, "interchange": False},
        {"name": "IGI Airport T3 Metro", "line": "Airport Express Line", "color": "#f97316", "lat": 28.5562, "lon": 77.0850, "interchange": False}
    ],

    "cafes": [
        # Central Delhi
        {"name": "Indian Coffee House", "area": "Connaught Place", "specialty": "Heritage Filter Coffee & Dosa", "rating": 4.3, "lat": 28.6310, "lon": 77.2172, "price": "₹"},
        {"name": "Blue Tokai Coffee Roasters", "area": "Connaught Place M-Block", "specialty": "Specialty Pour-over & Sourdough", "rating": 4.6, "lat": 28.6322, "lon": 77.2215, "price": "₹₹"},
        {"name": "United Coffee House", "area": "Connaught Place E-Block", "specialty": "Cona Coffee & Victorian Charm", "rating": 4.5, "lat": 28.6335, "lon": 77.2208, "price": "₹₹₹"},
        {"name": "Chaayos CP", "area": "F-Block Connaught Place", "specialty": "Desi Chai, Bun Maska & Snacks", "rating": 4.4, "lat": 28.6315, "lon": 77.2210, "price": "₹"},
        {"name": "Starbucks Hamilton House", "area": "Connaught Place Inner Circle", "specialty": "Frappuccinos & Cold Brew", "rating": 4.5, "lat": 28.6330, "lon": 77.2185, "price": "₹₹₹"},
        {"name": "Cafe Turtle", "area": "Khan Market", "specialty": "Organic Coffee, Salads & Books", "rating": 4.4, "lat": 28.6002, "lon": 77.2270, "price": "₹₹"},
        {"name": "The Big Chill Cafe", "area": "Khan Market", "specialty": "Thick Shakes, Cheesecakes & Pasta", "rating": 4.7, "lat": 28.6005, "lon": 77.2278, "price": "₹₹₹"},
        {"name": "Perch Wine & Coffee Bar", "area": "Khan Market", "specialty": "Vietnamese Coffee & Light Bites", "rating": 4.6, "lat": 28.6012, "lon": 77.2268, "price": "₹₹₹"},

        # South Delhi - AIIMS, Hauz Khas, Saket, Nehru Place
        {"name": "Chaayos Safdarjung / AIIMS", "area": "Opp. Safdarjung Hospital", "specialty": "Gur Chai & Kulhad Tea", "rating": 4.3, "lat": 28.5685, "lon": 77.2060, "price": "₹"},
        {"name": "Blue Tokai Coffee Roasters", "area": "Green Park Market", "specialty": "Nitro Cold Brew & Croissants", "rating": 4.7, "lat": 28.5592, "lon": 77.2072, "price": "₹₹"},
        {"name": "Third Wave Coffee", "area": "Green Park", "specialty": "Single Origin Espresso & Bagels", "rating": 4.5, "lat": 28.5585, "lon": 77.2060, "price": "₹₹"},
        {"name": "Hauz Khas Social", "area": "Hauz Khas Village", "specialty": "Craft Coffees, Lake View & Shakes", "rating": 4.5, "lat": 28.5540, "lon": 77.1945, "price": "₹₹"},
        {"name": "Kunzum Travel Cafe", "area": "Hauz Khas Village", "specialty": "Traveler Hangout & Coffee", "rating": 4.4, "lat": 28.5535, "lon": 77.1950, "price": "₹"},
        {"name": "Diggin", "area": "Anand Lok (Opp. Gargi College)", "specialty": "Brick Oven Pizza & Artisan Coffee", "rating": 4.6, "lat": 28.5512, "lon": 77.2230, "price": "₹₹"},
        {"name": "Chaayos Epicuria", "area": "Nehru Place Metro Complex", "specialty": "Shahi Chai & Loaded Parathas", "rating": 4.3, "lat": 28.5492, "lon": 77.2525, "price": "₹"},
        {"name": "Starbucks Epicuria", "area": "Nehru Place Metro Station", "specialty": "Caffe Latte & Caramel Macchiato", "rating": 4.5, "lat": 28.5496, "lon": 77.2530, "price": "₹₹₹"},
        {"name": "The Big Chill Cakery", "area": "Kailash Colony Market", "specialty": "Banoffee Pie & Iced Mocha", "rating": 4.7, "lat": 28.5535, "lon": 77.2415, "price": "₹₹"},
        {"name": "Blue Tokai Saidulajab", "area": "Champa Gali, Saket", "specialty": "Roastery, Flat White & Brownies", "rating": 4.7, "lat": 28.5185, "lon": 77.2010, "price": "₹₹"},
        {"name": "Jugmug Thela", "area": "Champa Gali, Saket", "specialty": "Artisan Teas, Coffee & Cookies", "rating": 4.4, "lat": 28.5182, "lon": 77.2012, "price": "₹₹"},
        {"name": "Rose Cafe", "area": "Westend Marg, Saidulajab", "specialty": "Vintage Victorian Tea & Cakes", "rating": 4.3, "lat": 28.5198, "lon": 77.1995, "price": "₹₹"},
        {"name": "Cafe Delhi Heights", "area": "DLF Avenue Saket", "specialty": "Juicy Lucy Burger & Smoothies", "rating": 4.5, "lat": 28.5270, "lon": 77.2185, "price": "₹₹₹"},
        {"name": "Carnatic Cafe", "area": "M-Block Greater Kailash II", "specialty": "Authentic Filter Kaapi & Dosas", "rating": 4.6, "lat": 28.5365, "lon": 77.2430, "price": "₹"},

        # North & East & West Delhi
        {"name": "AMA Cafe", "area": "Majnu Ka Tila (Tibetan Colony)", "specialty": "Himalayan Breakfast, Pancakes & Coffee", "rating": 4.7, "lat": 28.7018, "lon": 77.2285, "price": "₹₹"},
        {"name": "Rigo Restaurant & Cafe", "area": "Majnu Ka Tila", "specialty": "Tibetan Herbal Teas & Coffee", "rating": 4.4, "lat": 28.7022, "lon": 77.2290, "price": "₹"},
        {"name": "Hudson Cafe", "area": "Hudson Lane, GTB Nagar (DU)", "specialty": "Student Hangout, Shakes & Pasta", "rating": 4.4, "lat": 28.6985, "lon": 77.2052, "price": "₹"},
        {"name": "Big Yellow Door", "area": "GTB Nagar / North Campus", "specialty": "Cheesy Nachos & Cold Coffee", "rating": 4.3, "lat": 28.6990, "lon": 77.2058, "price": "₹"},
        {"name": "Cafe Coffee Day Kashmere Gate", "area": "Kashmere Gate ISBT", "specialty": "Espresso, Cappuccino & Quick Snacks", "rating": 4.0, "lat": 28.6672, "lon": 77.2280, "price": "₹"},
        {"name": "Chaayos Anand Vihar", "area": "Anand Vihar Railway Complex", "specialty": "Kulhad Chai & Samosa", "rating": 4.2, "lat": 28.6472, "lon": 77.3155, "price": "₹"},
        {"name": "Cafe Coffee Day Anand Vihar", "area": "ISBT Anand Vihar", "specialty": "Hot Chocolate & Brownie", "rating": 3.9, "lat": 28.6465, "lon": 77.3168, "price": "₹"},
        {"name": "Starbucks Punjabi Bagh", "area": "Club Road, Punjabi Bagh", "specialty": "Cold Brew & Sandwiches", "rating": 4.5, "lat": 28.6695, "lon": 77.1290, "price": "₹₹₹"},
        {"name": "Cafe Delhi Heights Janakpuri", "area": "Unity One Mall, Janakpuri", "specialty": "Signature Shakes & Platters", "rating": 4.4, "lat": 28.6290, "lon": 77.0780, "price": "₹₹"},

        # South-West, Airport & Border Corridors
        {"name": "Throttle Shrottle Moto Cafe", "area": "Faridabad-Gurugram Road / Kapashera Border", "specialty": "Biker Cafe, Masala Chai & Maggie", "rating": 4.3, "lat": 28.5140, "lon": 77.0820, "price": "₹₹"},
        {"name": "Cafe Coffee Day Badarpur", "area": "Mathura Road, Badarpur Border", "specialty": "Quick Transit Coffee & Muffins", "rating": 3.9, "lat": 28.4982, "lon": 77.3015, "price": "₹"},
        {"name": "Chaayos Badarpur", "area": "Near Badarpur Toll / Metro", "specialty": "Kadak Chai & Bun Omelette", "rating": 4.1, "lat": 28.4990, "lon": 77.3030, "price": "₹"},
        {"name": "Starbucks Aerocity", "area": "Worldmark 1, Aerocity", "specialty": "Reserve Blends & Gourmet Breakfast", "rating": 4.6, "lat": 28.5495, "lon": 77.1205, "price": "₹₹₹"},
        {"name": "Under The Neem", "area": "Vasant Kunj / Kapashera", "specialty": "Farm-to-Table Tea & Bakery", "rating": 4.5, "lat": 28.5320, "lon": 77.1420, "price": "₹₹₹"}
    ],

    "hospitals": [
        # Major Govt Apex Hospitals
        {"name": "AIIMS New Delhi (Apex Tertiary)", "area": "Ansari Nagar, Ring Road", "emergency": True, "type": "Government Apex", "beds": 2400, "lat": 28.5672, "lon": 77.2100, "phone": "011-26588500"},
        {"name": "Safdarjung Hospital & VMMC", "area": "Ring Road, Opp AIIMS", "emergency": True, "type": "Central Govt", "beds": 2800, "lat": 28.5680, "lon": 77.2065, "phone": "011-26707444"},
        {"name": "Dr. Ram Manohar Lohia (RML) Hospital", "area": "Baba Kharak Singh Marg, CP", "emergency": True, "type": "Central Govt", "beds": 1400, "lat": 28.6245, "lon": 77.2025, "phone": "011-23365525"},
        {"name": "Lok Nayak (LNJP) Hospital", "area": "Delhi Gate, JLN Marg", "emergency": True, "type": "Delhi Govt", "beds": 2000, "lat": 28.6398, "lon": 77.2395, "phone": "011-23236000"},
        {"name": "Guru Teg Bahadur (GTB) Hospital", "area": "Dilshad Garden, Shahdara", "emergency": True, "type": "Delhi Govt", "beds": 1700, "lat": 28.6830, "lon": 77.3110, "phone": "011-22586262"},
        {"name": "Deen Dayal Upadhyay (DDU) Hospital", "area": "Hari Nagar, Janakpuri", "emergency": True, "type": "Delhi Govt", "beds": 650, "lat": 28.6275, "lon": 77.1065, "phone": "011-25494401"},
        {"name": "Hindu Rao Hospital", "area": "Malka Ganj, near Kashmere Gate", "emergency": True, "type": "MCD Govt", "beds": 980, "lat": 28.6740, "lon": 77.2115, "phone": "011-23919476"},
        {"name": "St. Stephen's Hospital", "area": "Tis Hazari, Kashmere Gate", "emergency": True, "type": "Charitable Trust", "beds": 600, "lat": 28.6655, "lon": 77.2140, "phone": "011-23966021"},

        # Major South Delhi & Badarpur Corridors
        {"name": "Indraprastha Apollo Hospital", "area": "Sarita Vihar, Mathura Road (near Badarpur)", "emergency": True, "type": "Private Superspecialty", "beds": 710, "lat": 28.5360, "lon": 77.2885, "phone": "011-26925858"},
        {"name": "Batra Hospital & Medical Research Centre", "area": "1 Tughlakabad Institutional Area, MB Road", "emergency": True, "type": "Multispecialty", "beds": 500, "lat": 28.5135, "lon": 77.2485, "phone": "011-29958747"},
        {"name": "Max Super Speciality Hospital, Saket", "area": "Press Enclave Road, Saket", "emergency": True, "type": "Private Superspecialty", "beds": 530, "lat": 28.5275, "lon": 77.2120, "phone": "011-26515050"},
        {"name": "Fortis Escorts Heart Institute", "area": "Okhla Road, New Friends Colony", "emergency": True, "type": "Cardiac Apex", "beds": 310, "lat": 28.5605, "lon": 77.2760, "phone": "011-47135000"},
        {"name": "Holy Family Hospital", "area": "Okhla Road, Jamia Nagar", "emergency": True, "type": "Charitable Trust", "beds": 345, "lat": 28.5615, "lon": 77.2785, "phone": "011-26845900"},
        {"name": "Moolchand Medcity", "area": "Lajpat Nagar III, Ring Road", "emergency": True, "type": "Private Multispecialty", "beds": 300, "lat": 28.5662, "lon": 77.2340, "phone": "011-42000000"},
        {"name": "Pt. Madan Mohan Malaviya Hospital", "area": "Malviya Nagar, Saket", "emergency": True, "type": "Delhi Govt", "beds": 200, "lat": 28.5320, "lon": 77.2135, "phone": "011-26045330"},
        {"name": "Fortis Hospital, Vasant Kunj", "area": "Sector B, Pocket 1, Vasant Kunj", "emergency": True, "type": "Private Superspecialty", "beds": 200, "lat": 28.5285, "lon": 77.1550, "phone": "011-42776222"},
        {"name": "Institute of Liver & Biliary Sciences (ILBS)", "area": "Sector D-1, Vasant Kunj", "emergency": True, "type": "Autonomous Govt Apex", "beds": 180, "lat": 28.5085, "lon": 77.1585, "phone": "011-46300000"},

        # Central, West & North Hospitals
        {"name": "Sir Ganga Ram Hospital", "area": "Rajinder Nagar, Karol Bagh", "emergency": True, "type": "Private Multispecialty", "beds": 675, "lat": 28.6385, "lon": 77.1895, "phone": "011-25750000"},
        {"name": "BLK-Max Super Speciality Hospital", "area": "Pusa Road, Rajendra Place", "emergency": True, "type": "Private Superspecialty", "beds": 650, "lat": 28.6435, "lon": 77.1795, "phone": "011-30403040"},
        {"name": "Venkateshwar Hospital", "area": "Sector 18A, Dwarka", "emergency": True, "type": "Private Superspecialty", "beds": 325, "lat": 28.5910, "lon": 77.0375, "phone": "011-48555555"},
        {"name": "Manipal Hospital, Dwarka", "area": "Sector 6, Dwarka", "emergency": True, "type": "Private Superspecialty", "beds": 380, "lat": 28.5935, "lon": 77.0570, "phone": "011-49674967"},
        {"name": "Max Super Speciality Hospital, Patparganj", "area": "108 A, IP Extension, Patparganj (near Anand Vihar)", "emergency": True, "type": "Private Superspecialty", "beds": 400, "lat": 28.6305, "lon": 77.3055, "phone": "011-43033333"},
        {"name": "Fortis Hospital, Shalimar Bagh", "area": "AA Block, Poorbi Shalimar Bagh", "emergency": True, "type": "Private Superspecialty", "beds": 260, "lat": 28.7065, "lon": 77.1620, "phone": "011-45302222"},
        {"name": "Sanjay Gandhi Memorial Hospital", "area": "Mangolpuri, West Delhi", "emergency": True, "type": "Delhi Govt", "beds": 300, "lat": 28.6940, "lon": 77.0855, "phone": "011-27900100"},
        {"name": "Columbia Asia / Manipal Hospital Palam Vihar", "area": "Near Kapashera Border / Palam Vihar", "emergency": True, "type": "Private Multispecialty", "beds": 120, "lat": 28.5080, "lon": 77.0490, "phone": "0124-6165666"}
    ]
}

out_path = r'C:\Users\LENOVO\.gemini\antigravity\scratch\crowdedness-journey-planner\backend_data\poi_db.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(poi_db, f, indent=2)

print(f"Generated poi_db.json successfully!")
print(f"  Metros: {len(poi_db['metros'])}")
print(f"  Cafes: {len(poi_db['cafes'])}")
print(f"  Hospitals: {len(poi_db['hospitals'])}")
