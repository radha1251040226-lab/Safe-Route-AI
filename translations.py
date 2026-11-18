"""
SafeRouteAI - Multi-Lingual ADAS Voice & Warning System
Supports English, Hindi (हिंदी), Marathi (मराठी), Spanish (Español), French (Français), and German (Deutsch).
Provides native scripts for browser TTS and display, plus phonetic romanization for Windows SAPI desktop audio.
"""

SUPPORTED_LANGUAGES = {
    "English": {
        "code": "en",
        "locale": "en-US",
        "label": "🇬🇧 English",
        "voice_name": "English (US)",
    },
    "Hindi": {
        "code": "hi",
        "locale": "hi-IN",
        "label": "🇮🇳 Hindi (हिंदी)",
        "voice_name": "Hindi (India)",
    },
    "Marathi": {
        "code": "mr",
        "locale": "mr-IN",
        "label": "🇮🇳 Marathi (मराठी)",
        "voice_name": "Marathi (India)",
    },
    "Spanish": {
        "code": "es",
        "locale": "es-ES",
        "label": "🇪🇸 Spanish (Español)",
        "voice_name": "Spanish (Spain)",
    },
    "French": {
        "code": "fr",
        "locale": "fr-FR",
        "label": "🇫🇷 French (Français)",
        "voice_name": "French (France)",
    },
    "German": {
        "code": "de",
        "locale": "de-DE",
        "label": "🇩🇪 German (Deutsch)",
        "voice_name": "German (Germany)",
    },
}

# Master Translation Matrix
MESSAGES = {
    "CRITICAL_SNAKE_PREDATOR": {
        "English": "Critical hazard! Predator and venomous snake detected on ground! Remain inside vehicle with doors locked.",
        "Hindi": "अत्यधिक खतरा! शिकारी जानवर और जहरीला सांप देखा गया है! वाहन के अंदर रहें और दरवाजे बंद रखें।",
        "Marathi": "अतिशय धोका! हिंस्र प्राणी आणि विषारी साप आढळला आहे! गाडीतच राहा आणि दरवाजे बंद ठेवा.",
        "Spanish": "¡Peligro extremo! ¡Depredador y serpiente venenosa detectados! Permanezca dentro del vehículo con las puertas cerradas.",
        "French": "Danger extrême ! Prédateur et serpent venimeux détectés ! Restez dans le véhicule avec portes verrouillées.",
        "German": "Akute Gefahr! Raubtier und Giftschlange gesichtet! Im Fahrzeug bleiben und Türen verriegeln.",
        "phonetic_hi": "Atyadhik khatra! Shikari janwar aur zehreela saanp dekha gaya hai! Gadi ke andar rahein.",
        "phonetic_mr": "Atishay dhoka! Hinsa prani aani vishari saap aadhalla aahe! Gaaditach rahaa.",
    },
    "CRITICAL_SNAKE_GRASS": {
        "English": "Danger! Venomous snake detected on ground ahead! Do not exit vehicle or step on grass.",
        "Hindi": "खतरा! आगे जमीन पर जहरीला सांप देखा गया है! वाहन से बाहर न निकलें और घास पर पैर न रखें।",
        "Marathi": "धोका! पुढे जमिनीवर विषारी साप आढळला आहे! गाडीतून बाहेर पडू नका आणि गवतावर पाऊल ठेवू नका.",
        "Spanish": "¡Peligro! ¡Serpiente venenosa detectada en el suelo adelante! No baje del vehículo.",
        "French": "Danger ! Serpent venimeux détecté au sol devant ! Ne quittez pas le véhicule.",
        "German": "Gefahr! Giftschlange am Boden voraus gesichtet! Fahrzeug nicht verlassen.",
        "phonetic_hi": "Khatra! Aage zameen par zehreela saanp hai! Gadi se bahar na niklein.",
        "phonetic_mr": "Dhoka! Pudhe jaminivar vishari saap aahe! Gaaditun baher padu nakaa.",
    },
    "CRITICAL_SNAKE_ROAD": {
        "English": "Caution! Snake detected on road surface ahead! Stop and allow path to clear.",
        "Hindi": "सावधान! आगे सड़क पर सांप देखा गया है! वाहन रोकें और रास्ता साफ होने दें।",
        "Marathi": "सावधान! पुढे रस्त्यावर साप आढळला आहे! गाडी थांबवा आणि रस्ता मोकळा होऊ द्या.",
        "Spanish": "¡Atención! ¡Serpiente detectada en la carretera! Detenga el vehículo y espere a que despeje.",
        "French": "Attention ! Serpent détecté sur la chaussée ! Arrêtez-vous et laissez passer.",
        "German": "Achtung! Schlange auf der Fahrbahn erkannt! Anhalten und Straße freigeben.",
        "phonetic_hi": "Savdhan! Aage sadak par saanp hai! Gadi rokein aur rasta saaf hone dein.",
        "phonetic_mr": "Savdhan! Pudhe rastyavar saap aahe! Gaadi thambva aani rasta mokla hou dya.",
    },
    "CRITICAL_PREDATOR_SAVANNA": {
        "English": "Dry grass savanna terrain. High predator wildlife activity (Lion detected). Stay inside vehicle, do not exit.",
        "Hindi": "सवाना घास का मैदान। शेर की मौजूदगी पाई गई है। कृपया वाहन के अंदर ही रहें, बाहर न निकलें।",
        "Marathi": "गवताळ सव्हाना प्रदेश. सिंह आढळला आहे. कृपया गाडीतच राहा, बाहेर पडू नका.",
        "Spanish": "Terreno de sabana con hierba seca. Alta actividad de leones. Permanezca en el vehículo, no baje.",
        "French": "Terrain de savane avec herbes sèches. Présence de lion détectée. Restez dans le véhicule.",
        "German": "Savannengelände mit trockenem Gras. Löwensichtung. Unbedingt im Fahrzeug bleiben.",
        "phonetic_hi": "Savana ghas ka maidan. Sher ki maujoodgi hai. Kripya gadi ke andar hi rahein.",
        "phonetic_mr": "Gavtala pradesh. Sinha aadhalla aahe. Krupaya gaaditach rahaa.",
    },
    "CRITICAL_PREDATOR_ROAD": {
        "English": "Dangerous wildlife detected in driving path! Do not exit vehicle; stop and reverse safely.",
        "Hindi": "आगे खतरनाक जंगली जानवर देखा गया है! वाहन से बाहर न निकलें; सुरक्षित दूरी बनाकर पीछे हटें।",
        "Marathi": "पुढे रस्त्यावर धोकादायक वन्य प्राणी आहे! गाडीतून बाहेर पडू नका; सुरक्षितपणे मागे घ्या.",
        "Spanish": "¡Animal salvaje peligroso en el camino! No baje del vehículo; deténgase y retroceda con cuidado.",
        "French": "Animal sauvage dangereux sur la route ! Ne sortez pas ; arrêtez-vous et reculez prudemment.",
        "German": "Gefährliches Wildtier auf der Fahrbahn! Fahrzeug nicht verlassen; vorsichtig zurücksetzen.",
        "phonetic_hi": "Aage khatarnak janwar hai! Gadi se bahar na niklein, surakshit peeche hatein.",
        "phonetic_mr": "Pudhe dhokadayak prani aahe! Gaaditun baher padu naka, surakshit mage ghya.",
    },
    "CRITICAL_BRAKE_SLOW": {
        "English": "Danger ahead! Brake gently, slow down immediately, and proceed with extreme caution.",
        "Hindi": "आगे गंभीर खतरा! तुरंत ब्रेक लगाएं, गति धीमी करें और अत्यधिक सावधानी बरतें।",
        "Marathi": "पुढे गंभीर धोका! हळूच ब्रेक दाबा, वेग कमी करा आणि अत्यंत काळजीपूर्वक पुढे जा.",
        "Spanish": "¡Peligro inminente adelante! Frene suavemente, reduzca la velocidad y avance con precaución extrema.",
        "French": "Danger imminent ! Freinez doucement, ralentissez immédiatement et avancez avec grande prudence.",
        "German": "Gefahr voraus! Sanft abbremsen, sofort verlangsamen und mit äußerster Vorsicht fahren.",
        "phonetic_hi": "Aage bada khatra! Turant brake lagayein, dheere chalein aur savdhan rahein.",
        "phonetic_mr": "Pudhe gambhir dhoka! Halooch brake daba, veg kami kara aani kalji ghya.",
    },
    "PERSON_AND_POTHOLE": {
        "English": "Person and pothole detected ahead. Slow down and proceed carefully.",
        "Hindi": "आगे पैदल यात्री और सड़क का गड्ढा देखा गया है। गति धीमी करें और संभलकर चलें।",
        "Marathi": "पुढे पादचारी आणि रस्त्यावर खड्डा आढळला आहे. वेग कमी करा आणि सावकाश पुढे जा.",
        "Spanish": "Peatón y bache detectados al frente. Reduzca la velocidad y avance con cuidado.",
        "French": "Piéton et nid-de-poule détectés devant. Ralentissez et avancez prudemment.",
        "German": "Fußgänger und Schlagloch voraus erkannt. Geschwindigkeit reduzieren und vorsichtig fahren.",
        "phonetic_hi": "Aage paidal yatri aur gaddha hai. Gadi dheemi karein aur sambhalkar chalein.",
        "phonetic_mr": "Pudhe padachari aani khadda aahe. Veg kami kara aani savakash chala.",
    },
    "PEDESTRIAN_AHEAD": {
        "English": "Pedestrian in vicinity. Slow down, maintain safe gap, and stay alert.",
        "Hindi": "सड़क के पास पैदल यात्री हैं। गति धीमी करें, सुरक्षित दूरी रखें और सतर्क रहें।",
        "Marathi": "रस्त्याजवळ पादचारी आहेत. वेग कमी करा, सुरक्षित अंतर ठेवा आणि सतर्क राहा.",
        "Spanish": "Peatón cerca de la vía. Reduzca la velocidad, mantenga distancia y manténgase alerta.",
        "French": "Piéton à proximité. Ralentissez, maintenez une distance de sécurité et restez vigilant.",
        "German": "Fußgänger in der Nähe. Abbremsen, Sicherheitsabstand halten und aufmerksam bleiben.",
        "phonetic_hi": "Aage paidal yatri hain. Gadi dheemi karein aur surakshit doori banayein.",
        "phonetic_mr": "Rastyajaval padachari aahet. Veg kami kara aani surakshit antar theva.",
    },
    "ANIMAL_SAVANNA": {
        "English": "Dry grass off-road surface. Wild animals detected. Reduce speed and keep safe distance.",
        "Hindi": "कच्चा घास का रास्ता। जंगली जानवर देखे गए हैं। गति धीमी करें और सुरक्षित दूरी रखें।",
        "Marathi": "कच्चा गवताळ रस्ता. वन्य प्राणी आढळले आहेत. वेग कमी करा आणि सुरक्षित अंतर राखा.",
        "Spanish": "Superficie de hierba sin pavimentar. Animales salvajes detectados. Reduzca la velocidad.",
        "French": "Piste d'herbes sèches. Animaux sauvages détectés. Réduisez la vitesse et gardez vos distances.",
        "German": "Unbefestigter Grasboden. Wildtiere erkannt. Tempo drosseln und Abstand halten.",
        "phonetic_hi": "Kachha rasta hai. Janwar dekhe gaye hain. Dheere chalein aur doori rakhein.",
        "phonetic_mr": "Kachha gavtala rasta. Prani aadhalle aahet. Veg kami kara aani antar rakha.",
    },
    "ANIMAL_ROAD": {
        "English": "Animal detected on road ahead. Reduce speed and sound horn if necessary.",
        "Hindi": "आगे सड़क पर जानवर देखा गया है। गति धीमी करें और जरूरत पड़ने पर हॉर्न बजाएं।",
        "Marathi": "पुढे रस्त्यावर प्राणी आढळला आहे. वेग कमी करा आणि गरज पडल्यास हॉर्न वाजवा.",
        "Spanish": "Animal detectado en la carretera. Reduzca la velocidad y use la bocina si es necesario.",
        "French": "Animal détecté sur la route. Ralentissez et utilisez l'avertisseur si nécessaire.",
        "German": "Tier auf der Fahrbahn erkannt. Abbremsen und gegebenenfalls hupen.",
        "phonetic_hi": "Aage sadak par janwar hai. Gadi dheemi karein aur zaroorat padne par horn bajayein.",
        "phonetic_mr": "Pudhe rastyavar prani aahe. Veg kami kara aani garaj padlyas horn vajva.",
    },
    "DEEP_POTHOLES": {
        "English": "Deep potholes ahead. Brake gently and steer around them.",
        "Hindi": "आगे गहरे गड्ढे हैं। कृपया ब्रेक लगाएं और बचकर निकलें।",
        "Marathi": "पुढे खोल खड्डे आहेत. हळूच ब्रेक दाबा आणि बाजूने जा.",
        "Spanish": "Baches profundos adelante. Frene suavemente y esquívelos con cuidado.",
        "French": "Nids-de-poule profonds devant. Freinez doucement et contournez-les.",
        "German": "Tiefe Schlaglöcher voraus. Sanft abbremsen und vorsichtig umfahren.",
        "phonetic_hi": "Aage gahare gaddhe hain. Kripya brake lagayein aur bachkar niklein.",
        "phonetic_mr": "Pudhe khol khadde aahet. Halooch brake daba aani bajune jaa.",
    },
    "POTHOLE_NEARBY": {
        "English": "Pothole nearby. Reduce speed and maneuver carefully.",
        "Hindi": "पास में गड्ढा है। गति धीमी करें और सावधानी से गाड़ी निकालें।",
        "Marathi": "जवळच खड्डा आहे. वेग कमी करा आणि सावकाश वाहन चालवा.",
        "Spanish": "Bache cercano. Reduzca la velocidad y maniobre con precaución.",
        "French": "Nid-de-poule proche. Réduisez la vitesse et manœuvrez prudemment.",
        "German": "Schlagloch in der Nähe. Tempo drosseln und vorsichtig steuern.",
        "phonetic_hi": "Paas mein gaddha hai. Gadi dheemi karein aur savdhani se nikalein.",
        "phonetic_mr": "Javalach khadda aahe. Veg kami kara aani savakash chala.",
    },
    "STREAM_CRITICAL_CRATER": {
        "English": "Caution: Deep road craters ahead. Brake gently.",
        "Hindi": "सावधान: आगे सड़क पर बड़े गड्ढे हैं। कृपया धीरे चलाएं।",
        "Marathi": "सावधान: पुढे रस्त्यावर मोठे खड्डे आहेत. हळूच ब्रेक दाबा.",
        "Spanish": "Atención: Grandes baches en el camino. Frene con cuidado.",
        "French": "Attention : Grands nids-de-poule sur la route. Freinez prudemment.",
        "German": "Achtung: Tiefe Krater auf der Fahrbahn. Vorsichtig bremsen.",
        "phonetic_hi": "Savdhan: Aage bade gaddhe hain. Kripya dheere chalayein.",
        "phonetic_mr": "Savdhan: Pudhe mothe khadde aahet. Halooch brake daba.",
    },
    "STREAM_POTHOLE_SINGLE": {
        "English": "Road pothole detected. Drive carefully.",
        "Hindi": "सड़क पर गड्ढा देखा गया है। सावधानी से वाहन चलाएं।",
        "Marathi": "रस्त्यावर खड्डा आढळला आहे. सावकाश वाहन चालवा.",
        "Spanish": "Bache detectado en la carretera. Conduzca con precaución.",
        "French": "Nid-de-poule détecté sur la route. Conduisez prudemment.",
        "German": "Schlagloch erkannt. Vorsichtig weiterfahren.",
        "phonetic_hi": "Sadak par gaddha dekha gaya hai. Savdhani se chalayein.",
        "phonetic_mr": "Rastyavar khadda aadhalla aahe. Savakash gaadi chalva.",
    },
    "STREAM_POTHOLES_MULTI": {
        "English": "{count} road potholes detected. Drive carefully.",
        "Hindi": "सड़क पर {count} गड्ढे देखे गए हैं। कृपया वाहन धीरे चलाएं।",
        "Marathi": "रस्त्यावर {count} खड्डे आढळले आहेत. कृपया वाहन हळू चालवा.",
        "Spanish": "{count} baches detectados en la vía. Conduzca despacio.",
        "French": "{count} nids-de-poule détectés. Roulez lentement.",
        "German": "{count} Schlaglöcher erkannt. Langsam fahren.",
        "phonetic_hi": "Sadak par {count} gaddhe hain. Kripya gadi dheere chalayein.",
        "phonetic_mr": "Rastyavar {count} khadde aahet. Krupaya gaadi haloo chalva.",
    },
    "TRAFFIC_AHEAD": {
        "English": "Heavy vehicle presence. Maintain safe following distance.",
        "Hindi": "आगे भारी ट्रैफिक है। आगे वाले वाहन से सुरक्षित दूरी बनाए रखें।",
        "Marathi": "पुढे वाहनांची गर्दी आहे. पुढील वाहनापासून सुरक्षित अंतर ठेवा.",
        "Spanish": "Tráfico denso adelante. Mantenga distancia segura con el vehículo anterior.",
        "French": "Circulation dense devant. Gardez une distance de sécurité avec le véhicule qui précède.",
        "German": "Dichter Verkehr voraus. Ausreichenden Sicherheitsabstand einhalten.",
        "phonetic_hi": "Aage bhari traffic hai. Surakshit doori banaye rakhein.",
        "phonetic_mr": "Pudhe gardi aahe. Pudhil gaadipasun surakshit antar theva.",
    },
    "DRY_GRASS_TERRAIN": {
        "English": "Dry grass surface ahead. Maintain moderate speed on unpaved terrain.",
        "Hindi": "आगे कच्चा घास का रास्ता है। मध्यम गति से वाहन चलाएं।",
        "Marathi": "पुढे कच्चा गवताळ रस्ता आहे. मध्यम गतीने वाहन चालवा.",
        "Spanish": "Superficie de hierba seca adelante. Mantenga velocidad moderada.",
        "French": "Piste d'herbe sèche devant. Maintenez une vitesse modérée.",
        "German": "Trockenes Grasgelände voraus. Mäßige Geschwindigkeit beibehalten.",
        "phonetic_hi": "Aage kachha ghas ka rasta hai. Madhyam gati se chalein.",
        "phonetic_mr": "Pudhe kachha gavtala rasta aahe. Madhyam gatine chala.",
    },
    "PATH_CLEAR": {
        "English": "Path is clear. Maintain normal driving speed.",
        "Hindi": "रास्ता साफ है। सामान्य गति से चलते रहें।",
        "Marathi": "रस्ता मोकळा आहे. सामान्य गतीने प्रवास सुरू ठेवा.",
        "Spanish": "Camino despejado. Mantenga velocidad normal de crucero.",
        "French": "Voie libre. Maintenez la vitesse normale.",
        "German": "Weg ist frei. Normale Reisegeschwindigkeit beibehalten.",
        "phonetic_hi": "Rasta saaf hai. Samanya gati se chalte rahein.",
        "phonetic_mr": "Rasta mokla aahe. Samanya gatine pravas chalu theva.",
    },
    "ROAD_CLEAR": {
        "English": "Road surface clear.",
        "Hindi": "सड़क साफ है।",
        "Marathi": "रस्ता स्वच्छ व सुरक्षित आहे.",
        "Spanish": "Superficie despejada.",
        "French": "Chaussée dégagée.",
        "German": "Fahrbahn frei.",
        "phonetic_hi": "Sadak saaf hai.",
        "phonetic_mr": "Rasta mokla aani surakshit aahe.",
    },
    "SCANNING": {
        "English": "Scanning road ahead...",
        "Hindi": "सड़क की जांच की जा रही है...",
        "Marathi": "रस्त्याची तपासणी सुरू आहे...",
        "Spanish": "Escaneando carretera...",
        "French": "Analyse de la route en cours...",
        "German": "Straße wird gescannt...",
        "phonetic_hi": "Sadak ki jaanch ki ja rahi hai...",
        "phonetic_mr": "Rastyachi tapasni suru aahe...",
    },
}

# UI Speed Advisories
SPEED_ADVISORIES = {
    "red": {
        "English": "🚨 SPEED ADVISORY: < 15 KM/H (EMERGENCY SLOW / STOP)",
        "Hindi": "🚨 गति सलाह: < 15 किमी/घंटा (तुरंत धीमा करें / रुकें)",
        "Marathi": "🚨 वेग सल्ला: < 15 किमी/तास (त्वरित हळू करा / थांबा)",
        "Spanish": "🚨 AVISO DE VELOCIDAD: < 15 KM/H (FRENO DE EMERGENCIA)",
        "French": "🚨 VITESSE CONSEILLÉE : < 15 KM/H (RALENTISSEMENT D'URGENCE)",
        "German": "🚨 TEMPO-EMPFEHLUNG: < 15 KM/H (NOTFALL-STOPP)",
    },
    "orange": {
        "English": "⚠️ SPEED ADVISORY: 30-40 KM/H (CAUTION PACE)",
        "Hindi": "⚠️ गति सलाह: 30-40 किमी/घंटा (सतर्क गति)",
        "Marathi": "⚠️ वेग सल्ला: 30-40 किमी/तास (सावध वेग)",
        "Spanish": "⚠️ AVISO DE VELOCIDAD: 30-40 KM/H (PRECAUCIÓN)",
        "French": "⚠️ VITESSE CONSEILLÉE : 30-40 KM/H (PRUDENCE)",
        "German": "⚠️ TEMPO-EMPFEHLUNG: 30-40 KM/H (VORSICHTIGES TEMPO)",
    },
    "green": {
        "English": "🛡️ SPEED ADVISORY: 60 KM/H (CRUISE SPEED)",
        "Hindi": "🛡️ गति सलाह: 60 किमी/घंटा (सामान्य गति)",
        "Marathi": "🛡️ वेग सल्ला: 60 किमी/तास (सामान्य वेग)",
        "Spanish": "🛡️ AVISO DE VELOCIDAD: 60 KM/H (CRUCERO SEGURO)",
        "French": "🛡️ VITESSE CONSEILLÉE : 60 KM/H (VITESSE DE CROISIÈRE)",
        "German": "🛡️ TEMPO-EMPFEHLUNG: 60 KM/H (REISEGESCHWINDIGKEIT)",
    },
}

# Risk Level Badges
RISK_LEVEL_LABELS = {
    "CRITICAL": {
        "English": "CRITICAL RISK ADVISORY",
        "Hindi": "अत्यधिक गंभीर खतरा",
        "Marathi": "अतिशय गंभीर धोका",
        "Spanish": "AVISO DE RIESGO CRÍTICO",
        "French": "ALERTE DE RISQUE CRITIQUE",
        "German": "KRITISCHE GEFAHRENWARNUNG",
    },
    "HIGH": {
        "English": "HIGH RISK ADVISORY",
        "Hindi": "उच्च जोखिम चेतावनी",
        "Marathi": "उच्च धोका इशारा",
        "Spanish": "AVISO DE ALTO RIESGO",
        "French": "ALERTE DE RISQUE ÉLEVÉ",
        "German": "HOHE GEFAHRENWARNUNG",
    },
    "MEDIUM": {
        "English": "MODERATE RISK ADVISORY",
        "Hindi": "मध्यम जोखिम चेतावनी",
        "Marathi": "मध्यम धोका इशारा",
        "Spanish": "AVISO DE RIESGO MODERADO",
        "French": "ALERTE DE RISQUE MODÉRÉ",
        "German": "MÄSSIGE GEFAHRENWARNUNG",
    },
    "LOW": {
        "English": "CLEAR ROUTE ADVISORY",
        "Hindi": "सुरक्षित मार्ग सूचना",
        "Marathi": "सुरक्षित मार्ग सूचना",
        "Spanish": "AVISO DE RUTA DESPEJADA",
        "French": "ROUTE DÉGAGÉE",
        "German": "FREIE FAHRT",
    },
}


from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class LanguageMetadata:
    """Encapsulates language configuration metadata."""
    code: str
    locale: str
    label: str
    voice_name: str


@dataclass(frozen=True)
class TranslationResult:
    """Encapsulates translated text and speech payload."""
    text: str
    speech_browser: str
    speech_system: str
    locale: str

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like access for backward compatibility."""
        return getattr(self, key, default)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class LocalizationService:
    """
    Object-Oriented Localization Service.
    Encapsulates translations, speech adaptations, and language metadata.
    """

    def __init__(self, languages: Optional[Dict[str, Any]] = None, messages: Optional[Dict[str, Any]] = None):
        self._languages = languages or SUPPORTED_LANGUAGES
        self._messages = messages or MESSAGES
        self._speed_advisories = SPEED_ADVISORIES
        self._risk_labels = RISK_LEVEL_LABELS

    @property
    def supported_languages(self) -> Dict[str, Any]:
        """Returns read-only view of supported languages."""
        return self._languages

    def get_locale(self, language: str = "English") -> str:
        """Retrieves BCP 47 locale code for a language."""
        lang_info = self._languages.get(language, self._languages.get("English", {}))
        return lang_info.get("locale", "en-US")

    def translate(self, key: str, language: str = "English", **kwargs) -> TranslationResult:
        """
        Translates a message key into target language with phonetic system speech.
        """
        locale = self.get_locale(language)
        entry = self._messages.get(key, {})
        raw_text = entry.get(language) or entry.get("English", key)

        if kwargs:
            try:
                formatted_text = raw_text.format(**kwargs)
            except Exception:
                formatted_text = raw_text
        else:
            formatted_text = raw_text

        # Phonetic romanization for Windows SAPI desktop audio
        if language == "Hindi" and "phonetic_hi" in entry:
            system_text = entry["phonetic_hi"].format(**kwargs) if kwargs else entry["phonetic_hi"]
        elif language == "Marathi" and "phonetic_mr" in entry:
            system_text = entry["phonetic_mr"].format(**kwargs) if kwargs else entry["phonetic_mr"]
        else:
            system_text = formatted_text

        return TranslationResult(
            text=formatted_text,
            speech_browser=formatted_text,
            speech_system=system_text,
            locale=locale
        )

    def get_speed_advisory(self, color: str, language: str = "English") -> str:
        """Retrieves localized speed advisory."""
        entry = self._speed_advisories.get(color, self._speed_advisories.get("green", {}))
        return entry.get(language, entry.get("English", ""))

    def get_risk_label(self, risk_level: str, language: str = "English") -> str:
        """Retrieves localized risk badge label."""
        entry = self._risk_labels.get(risk_level, self._risk_labels.get("LOW", {}))
        return entry.get(language, entry.get("English", ""))


# Singleton instance
localization_service = LocalizationService()


# Backward Compatibility Facade Functions
def get_translation(key: str, language: str = "English", **kwargs) -> Dict[str, Any]:
    res = localization_service.translate(key, language=language, **kwargs)
    return {
        "text": res.text,
        "speech_browser": res.speech_browser,
        "speech_system": res.speech_system,
        "locale": res.locale
    }


def get_speed_advisory(color: str, language: str = "English") -> str:
    return localization_service.get_speed_advisory(color, language=language)


def get_risk_label(risk_level: str, language: str = "English") -> str:
    return localization_service.get_risk_label(risk_level, language=language)
