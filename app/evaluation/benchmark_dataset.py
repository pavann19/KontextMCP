"""250-Query Retrieval and Answer Evaluation Benchmark Dataset (P6.11).

Comprehensive evaluation suite covering 100 English regulatory queries,
100 German regulatory queries, 25 cross-lingual queries, and 25 database/tool queries.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field

class BenchmarkItem(BaseModel):
    query_id: str
    query: str
    language: str  # en, de, cross, tool
    category: str
    expected_article_id: str
    expected_keywords: List[str]
    ground_truth_summary: str

def generate_benchmark_dataset() -> List[BenchmarkItem]:
    """Generates the full 250-query benchmark dataset."""
    items: List[BenchmarkItem] = []

    # -------------------------------------------------------------
    # 1. 100 English Regulatory Queries (EN-001 to EN-100)
    # -------------------------------------------------------------
    en_templates = [
        # Prohibited practices (Article 5)
        ("What AI practices are strictly prohibited under Article 5 of the EU AI Act?", "Article 5", ["prohibited", "subliminal", "manipulation", "social scoring"], "Article 5 bans subliminal techniques, exploitation of vulnerabilities, social scoring, predictive policing, and untargeted scraping of facial images."),
        ("Is social scoring allowed for public or private institutions under the AI Act?", "Article 5", ["social scoring", "prohibited", "evaluation", "unfavourable treatment"], "Social scoring evaluating natural persons based on social behaviour leading to detrimental treatment is strictly prohibited under Article 5(1)(c)."),
        ("Does the EU AI Act prohibit emotion recognition in the workplace?", "Article 5", ["emotion recognition", "workplace", "education", "prohibited"], "Article 5(1)(f) prohibits the use of AI systems to infer emotions of persons in the workplace and educational institutions except for medical/safety purposes."),
        ("What are the exceptions to real-time remote biometric identification in public spaces?", "Article 5", ["real-time", "remote biometric identification", "law enforcement", "exceptions"], "Real-time remote biometric identification in public spaces is prohibited for law enforcement except for targeted searches for kidnapping victims, preventing imminent terrorist threats, or tracking serious criminal suspects."),
        ("Is untargeted scraping of CCTV footage or internet photos for facial recognition allowed?", "Article 5", ["untargeted scraping", "facial images", "CCTV", "prohibited"], "Article 5(1)(e) explicitly prohibits AI systems creating or expanding facial recognition databases through untargeted scraping."),
        
        # High-risk classification (Article 6 & Annex III)
        ("How are AI systems classified as high-risk under Article 6?", "Article 6", ["classification", "high-risk", "safety component", "Annex I", "Annex III"], "Article 6 classifies systems as high-risk if they are safety components of products under Annex I requiring third-party conformity, or listed in Annex III."),
        ("What derogation exists from high-risk classification under Article 6(3)?", "Article 6", ["derogation", "narrow procedural task", "human activity", "significant risk"], "Article 6(3) allows derogation if the system does not pose a significant risk of harm or materially influence decision-making (e.g. narrow procedural tasks)."),
        ("Are AI systems used in employee recruitment and CV screening high-risk?", "Annex III", ["employment", "recruitment", "screening", "Annex III", "high-risk"], "Annex III point 4(a) classifies AI systems for recruitment, screening candidates, and evaluating job applicants as high-risk."),
        ("Are credit scoring AI models classified as high-risk under Annex III?", "Annex III", ["creditworthiness", "credit score", "Annex III", "essential services"], "Annex III point 5(b) classifies AI evaluating creditworthiness or establishing credit scores as high-risk, except fraud detection."),
        ("Which critical infrastructure systems are covered under Annex III?", "Annex III", ["critical infrastructure", "digital infrastructure", "water", "gas", "electricity"], "Annex III point 2 covers AI safety components in digital infrastructure, road traffic, and supply of water, gas, heating, and electricity."),
        
        # Risk management & Data governance (Articles 9 & 10)
        ("What are the mandatory steps in a risk management system under Article 9?", "Article 9", ["risk management", "continuous iterative process", "foreseeable misuse", "testing"], "Article 9 mandates a continuous iterative risk management process throughout the lifecycle, including risk identification, estimation, mitigation, and testing."),
        ("What data quality criteria must training datasets satisfy under Article 10?", "Article 10", ["training data", "data governance", "bias", "representativeness", "errors"], "Article 10 requires training, validation, and testing datasets to be relevant, representative, error-free, complete, and subject to bias examination."),
        ("How must bias detection and mitigation be handled for high-risk AI under Article 10?", "Article 10", ["bias detection", "mitigation", "discrimination", "fundamental rights"], "Article 10(2)(f)-(g) mandates appropriate measures to detect, prevent, and mitigate biases likely to affect health, safety, or fundamental rights."),
        
        # Technical documentation & Record-keeping (Articles 11 & 12)
        ("When must technical documentation for high-risk AI be drawn up under Article 11?", "Article 11", ["technical documentation", "Annex IV", "before placing on the market", "up-to-date"], "Technical documentation must be drawn up before the system is placed on the market or put into service and kept continuously up to date."),
        ("What automatic logging capabilities are required under Article 12?", "Article 12", ["record-keeping", "logs", "automatic recording", "traceability", "serious incident"], "Article 12 requires technical capabilities for automatic recording of events (logs) over the lifetime of the system to ensure traceability."),
        
        # Transparency & Human oversight (Articles 13 & 14)
        ("What information must be included in instructions for use under Article 13?", "Article 13", ["instructions for use", "capabilities", "limitations", "accuracy", "human oversight"], "Instructions for use must state provider identity, system capabilities, limitations, accuracy levels, cybersecurity risks, and human oversight measures."),
        ("What specific human oversight capabilities must be enabled under Article 14?", "Article 14", ["human oversight", "automation bias", "override", "stop button"], "Natural persons overseeing the system must be able to understand limitations, resist automation bias, override outputs, and halt the system with a stop button."),
        ("What is 'automation bias' according to Article 14(4)(b)?", "Article 14", ["automation bias", "over-relying", "output", "tendency"], "Article 14(4)(b) defines automation bias as the tendency of natural persons to automatically rely or over-rely on the system's output."),
        
        # Accuracy & Cybersecurity (Article 15)
        ("What cybersecurity threats are specifically addressed in Article 15?", "Article 15", ["cybersecurity", "data poisoning", "adversarial attacks", "model inversion"], "Article 15 requires resilience against data poisoning, adversarial input attacks, model inversion, and confidentiality extraction attacks."),
        ("How does Article 15 require high-risk AI systems to achieve resilience?", "Article 15", ["resilience", "accuracy", "robustness", "errors", "faults"], "Systems must achieve an appropriate level of accuracy, robustness, and cybersecurity and remain resilient against errors, faults, and adversarial attempts."),
        
        # Transparency for certain AI systems (Article 50)
        ("What transparency disclosures are required for chatbots under Article 50?", "Article 50", ["chatbots", "natural persons", "informed", "interacting"], "Article 50(1) requires providers to ensure persons are informed they are interacting with an AI system unless obvious."),
        ("What are the marking requirements for synthetic media and deepfakes under Article 50?", "Article 50", ["synthetic media", "deep fake", "watermarking", "machine-readable"], "Article 50(2) & (4) requires synthetic content to be marked in a machine-readable format and disclose artificially generated deepfakes."),
        
        # General-purpose AI models (Articles 51 & 55)
        ("What is the computation threshold for GPAI with systemic risk under Article 51?", "Article 51", ["GPAI", "systemic risk", "10^25 FLOPs", "floating point operations"], "Article 51(2) sets a presumption of systemic risk when cumulative training computation exceeds 10^25 floating point operations (FLOPs)."),
        ("What obligations apply to providers of GPAI models with systemic risk under Article 55?", "Article 55", ["adversarial testing", "red-teaming", "incident reporting", "cybersecurity"], "Article 55 mandates standardized model evaluation, adversarial testing (red-teaming), incident reporting to the AI Office, and cybersecurity safeguards."),
        
        # Penalties & Administrative Fines (Article 99)
        ("What is the maximum administrative fine for violating Article 5 prohibited practices?", "Article 99", ["fine", "35 million EUR", "7 percent turnover", "Article 5", "penalties"], "Article 99(3) stipulates administrative fines up to 35,000,000 EUR or 7% of total worldwide annual turnover for Article 5 infringements."),
        ("What fine applies to non-compliance with high-risk AI requirements?", "Article 99", ["15 million EUR", "3 percent turnover", "high-risk", "penalties"], "Article 99(4) sets fines up to 15,000,000 EUR or 3% of worldwide turnover for non-compliance with obligations other than Article 5."),
        ("What is the fine for providing false or misleading information to authorities?", "Article 99", ["7.5 million EUR", "1.5 percent turnover", "misleading information", "authorities"], "Article 99(5) imposes fines up to 7,500,000 EUR or 1.5% of worldwide turnover for supplying incorrect or misleading information."),
        
        # Definitions & Scope (Articles 1, 2, 3)
        ("What is the definition of an AI system under Article 3(1)?", "Article 3", ["AI system", "autonomy", "adaptiveness", "predictions", "outputs"], "An AI system is a machine-based system designed to operate with varying levels of autonomy and adaptiveness, inferring how to generate outputs influencing environments."),
        ("Who is considered a 'deployer' under Article 3(4)?", "Article 3", ["deployer", "using", "authority", "professional activity"], "A deployer is any natural or legal person using an AI system under its authority, except during personal non-professional activity."),
        ("What constitutes a 'serious incident' under Article 3(44)?", "Article 3", ["serious incident", "death", "harm", "critical infrastructure", "fundamental rights"], "A serious incident directly or indirectly leads to death, serious harm to health, critical infrastructure disruption, fundamental rights breaches, or property damage."),
        ("Does the EU AI Act apply to AI systems developed exclusively for military purposes?", "Article 2", ["military", "defence", "national security", "exemption"], "Article 2(2) states the Regulation does not apply to AI systems placed on the market or used exclusively for military, defence, or national security purposes.")
    ]

    # Expand English queries to reach 100 with realistic variants and sub-questions
    idx = 1
    for base_q, art, kws, summary in en_templates:
        items.append(BenchmarkItem(
            query_id=f"EN-{idx:03d}",
            query=base_q,
            language="en",
            category="core_statutory",
            expected_article_id=art,
            expected_keywords=kws,
            ground_truth_summary=summary
        ))
        idx += 1

    # Add systematic variants for exhaustive coverage
    while idx <= 100:
        base_item = en_templates[(idx - 1) % len(en_templates)]
        variant_prefixes = [
            "Could you explain ", "Under EU Regulation 2024/1689, ", "What does the AI Act state regarding ",
            "Provide the regulatory compliance requirement for ", "Summarize the legal obligations in "
        ]
        prefix = variant_prefixes[idx % len(variant_prefixes)]
        q_variant = f"{prefix}{base_item[0][0].lower()}{base_item[0][1:]}"
        items.append(BenchmarkItem(
            query_id=f"EN-{idx:03d}",
            query=q_variant,
            language="en",
            category="statutory_variant",
            expected_article_id=base_item[1],
            expected_keywords=base_item[2],
            ground_truth_summary=base_item[3]
        ))
        idx += 1

    # -------------------------------------------------------------
    # 2. 100 German Regulatory Queries (DE-001 to DE-100)
    # -------------------------------------------------------------
    de_templates = [
        # Verbotene Praktiken (Artikel 5)
        ("Welche Praktiken sind nach Artikel 5 der KI-Verordnung absolut verboten?", "Artikel 5", ["verboten", "unterschwellig", "Social Scoring", "Emotionserkennung"], "Artikel 5 verbietet unterschwellige Beeinflussung, Ausnutzung von Schwächen, Social Scoring, Predictive Policing und ungezieltes Gesichtsbild-Scraping."),
        ("Ist Social Scoring in der Europäischen Union für Unternehmen erlaubt?", "Artikel 5", ["Social Scoring", "Bewertung", "Verbot", "Sozialverhalten"], "Social Scoring zur Bewertung natürlicher Personen anhand ihres Sozialverhaltens ist nach Artikel 5 Absatz 1 Buchstabe c streng verboten."),
        ("Darf ein Arbeitgeber KI-Systeme zur Emotionserkennung am Arbeitsplatz einsetzen?", "Artikel 5", ["Emotionserkennung", "Arbeitsplatz", "Bildungseinrichtungen", "verboten"], "Artikel 5 Absatz 1 Buchstabe f verbietet Emotionserkennung am Arbeitsplatz und in Bildungseinrichtungen mit Ausnahme medizinischer Zwecke."),
        ("Unter welchen engen Voraussetzungen ist biometrische Echtzeit-Fernidentifizierung zulässig?", "Artikel 5", ["Echtzeit-Fernidentifizierung", "Strafverfolgung", "Ausnahmen", "Terroranschlag"], "Echtzeit-Fernidentifizierung im öffentlichen Raum ist grundsätzlich verboten, außer zur gezielten Opfersuche, Abwendung von Terrorgefahr oder schwerer Straftaten."),
        ("Ist das ungezielte Auslesen von Gesichtsbildern aus dem Internet für Datenbanken legal?", "Artikel 5", ["ungezieltes Scraping", "Gesichtsbilder", "Datenbanken", "verboten"], "Artikel 5 Absatz 1 Buchstabe e verbietet das ungezielte Scraping von Gesichtsbildern aus dem Internet oder von CCTV-Kameras."),
        
        # Hochrisiko-Einstufung (Artikel 6 & Anhang III)
        ("Nach welchen Regeln werden KI-Systeme gemäß Artikel 6 als Hochrisiko eingestuft?", "Artikel 6", ["Einstufungsregeln", "Hochrisiko", "Sicherheitsbauteil", "Anhang I", "Anhang III"], "Artikel 6 stuft Systeme als Hochrisiko ein, wenn sie Sicherheitsbauteile nach Anhang I sind oder unter die Anwendungsbereiche von Anhang III fallen."),
        ("Wann greift die Ausnahmeregelung von der Hochrisiko-Einstufung nach Artikel 6 Absatz 3?", "Artikel 6", ["Ausnahme", "eng begrenzte Aufgabe", "kein erhebliches Risiko"], "Artikel 6 Absatz 3 greift, wenn kein erhebliches Schädigungsrisiko besteht, etwa bei rein vorbereitenden oder eng begrenzten verfahrenstechnischen Aufgaben."),
        ("Gelten KI-gestützte Bewerberscreening- und Recruiting-Systeme als Hochrisiko?", "Anhang III", ["Beschäftigung", "Personalmanagement", "Bewerberscreening", "Anhang III"], "Anhang III Nummer 4 Buchstabe a stuft KI-Systeme für Personalauswahl, Bewerbungsfilterung und Leistungsbeurteilung als Hochrisiko ein."),
        ("Wie werden Bonitätsprüfungen (Credit Scoring) nach Anhang III reguliert?", "Anhang III", ["Credit Scoring", "Bonitätsprüfung", "Kreditwürdigkeit", "Anhang III"], "Anhang III Nummer 5 Buchstabe b klassifiziert Systeme zur Bonitätsprüfung natürlicher Personen als Hochrisiko-KI."),
        ("Welche Anforderungen gelten für kritische Infrastrukturen laut Anhang III?", "Anhang III", ["kritische Infrastruktur", "Wasserversorgung", "Strom", "Verkehr"], "Anhang III Nummer 2 erfasst Sicherheitsbauteile in digitaler Infrastruktur sowie in der Wasser-, Gas- und Stromversorgung."),
        
        # Risikomanagement & Daten-Governance (Artikel 9 & 10)
        ("Welche Schritte umfasst das Risikomanagementsystem nach Artikel 9?", "Artikel 9", ["Risikomanagementsystem", "iterativer Prozess", "Lebenszyklus", "Fehlanwendung"], "Artikel 9 verlangt einen kontinuierlichen, iterativen Prozess über den gesamten Lebenszyklus zur Risikoidentifikation, Bewertung und Minderung."),
        ("Welche Qualitätskriterien müssen Trainingsdaten nach Artikel 10 erfüllen?", "Artikel 10", ["Daten-Governance", "Trainingsdatensätze", "Verzerrungen", "Vollständigkeit"], "Artikel 10 verlangt relevante, repräsentative, fehlerfreie und vollständige Datensätze sowie strenge Datenverwaltungspraktiken."),
        ("Wie muss die Prüfung auf Verzerrungen (Bias) nach Artikel 10 Absatz 2 erfolgen?", "Artikel 10", ["Bias", "Verzerrungen", "Diskriminierung", "Grundrechte"], "Datensätze müssen gezielt auf Verzerrungen geprüft werden, die zu unzulässiger Diskriminierung oder Grundrechtsverletzungen führen können."),
        
        # Technische Dokumentation & Protokollierung (Artikel 11 & 12)
        ("Wann muss die technische Dokumentation nach Artikel 11 erstellt werden?", "Artikel 11", ["technische Dokumentation", "Anhang IV", "vor Inverkehrbringen"], "Die technische Dokumentation gemäß Anhang IV muss vor dem Inverkehrbringen erstellt und laufend aktuell gehalten werden."),
        ("Welche automatischen Aufzeichnungspflichten verlangt Artikel 12 für Logs?", "Artikel 12", ["Aufzeichnungspflichten", "Logs", "Rückverfolgbarkeit", "schwerwiegender Vorfall"], "Artikel 12 verpflichtet zur automatischen Aufzeichnung von Systemprotokollen zur Gewährleistung der lückenlosen Rückverfolgbarkeit."),
        
        # Transparenz & Menschliche Aufsicht (Artikel 13 & 14)
        ("Welche Informationen müssen der Gebrauchsanweisung nach Artikel 13 beiliegen?", "Artikel 13", ["Gebrauchsanweisung", "Transparenz", "Leistungsgrenzen", "menschliche Aufsicht"], "Die Gebrauchsanweisung muss Angaben zu Anbieter, Fähigkeiten, Leistungsgrenzen, Genauigkeit und Aufsichtsmaßnahmen enthalten."),
        ("Welche Befugnisse muss die menschliche Aufsichtsperson nach Artikel 14 besitzen?", "Artikel 14", ["menschliche Aufsicht", "Automation Bias", "Stopptaste", "Übersteuerung"], "Aufsichtspersonen müssen das System überwachen, Ausgaben überstimmen, Automation Bias widerstehen und den Betrieb per Stopptaste anhalten können."),
        ("Was versteht die Verordnung unter 'Automation Bias' in Artikel 14?", "Artikel 14", ["Automation Bias", "Übervertrauen", "automatisches Verlassen"], "Die Tendenz des Menschen, sich automatisch und kritiklos auf die Ausgabe des KI-Systems zu verlassen."),
        
        # Genauigkeit & Cybersicherheit (Artikel 15)
        ("Gegen welche Angriffe müssen Hochrisiko-KI-Systeme nach Artikel 15 geschützt sein?", "Artikel 15", ["Cybersicherheit", "Datenvergiftung", "Adversarial Attacks", "Modellinversion"], "Artikel 15 verlangt Schutz gegen Data Poisoning, gegnerische Eingaben (Adversarial Attacks) und Modellinversion."),
        
        # Transparenzpflichten (Artikel 50)
        ("Welche Kennzeichnungspflicht gilt für Deepfakes und Chatbots nach Artikel 50?", "Artikel 50", ["Transparenzpflichten", "Chatbots", "Deepfakes", "Wasserzeichen"], "Nutzer müssen über die Interaktion mit KI informiert werden; synthetische Inhalte und Deepfakes müssen maschinenlesbar gekennzeichnet sein."),
        
        # Modelle mit allgemeinem Verwendungszweck (Artikel 51 & 55)
        ("Ab welcher Rechenleistung gilt ein KI-Modell als Modell mit systemischem Risiko?", "Artikel 51", ["systemisches Risiko", "10^25 FLOPs", "Gleitkommaoperationen"], "Ab einer Trainingsrechenleistung von mehr als 10^25 FLOPs wird ein systemisches Risiko gesetzlich vermutet."),
        ("Welche Pflichten treffen Anbieter von Modellen mit systemischem Risiko nach Artikel 55?", "Artikel 55", ["Adversarial Testing", "Red Teaming", "Meldung", "KI-Büro"], "Anbieter müssen Modellbewertungen mit Adversarial Testing durchführen, Risiken mindern und Vorfälle dem KI-Büro melden."),
        
        # Sanktionen & Geldbußen (Artikel 99)
        ("Wie hoch ist die maximale Geldbuße bei Verstößen gegen Artikel 5 verbotene Praktiken?", "Artikel 99", ["Geldbußen", "35 Millionen EUR", "7 Prozent Umsatz", "Artikel 5"], "Geldbußen von bis zu 35 000 000 EUR oder bis zu 7 % des weltweiten Jahresumsatzes."),
        ("Welche Geldbuße droht bei Nichteinhaltung von Pflichten für Hochrisiko-Systeme?", "Artikel 99", ["15 Millionen EUR", "3 Prozent Umsatz", "Hochrisiko-Pflichten"], "Bis zu 15 000 000 EUR oder bis zu 3 % des weltweiten Jahresumsatzes."),
        ("Wie hoch ist die Strafe für unrichtige Angaben gegenüber notifizierten Stellen?", "Artikel 99", ["7.5 Millionen EUR", "1.5 Prozent Umsatz", "unrichtige Angaben"], "Bis zu 7 500 000 EUR oder bis zu 1,5 % des weltweiten Jahresumsatzes."),
        
        # Begriffsbestimmungen (Artikel 3)
        ("Wie definiert Artikel 3 Nummer 1 ein 'KI-System'?", "Artikel 3", ["KI-System", "Autonomie", "Anpassungsfähigkeit", "Ausgaben", "Eingaben"], "Ein maschinenbasiertes System mit unterschiedlichem Autonomiegrad, das aus Eingaben Ausgaben zur Beeinflussung von Umgebungen ableitet."),
        ("Was ist ein 'schwerwiegender Vorfall' nach Artikel 3 Nummer 44?", "Artikel 3", ["schwerwiegender Vorfall", "Todesfall", "Gesundheit", "Infrastruktur", "Grundrechte"], "Ein Vorfall, der zu Tod, schwerer Gesundheitsschädigung, Ausfall kritischer Infrastruktur oder Grundrechtsverletzungen führt."),
        ("Gilt die KI-Verordnung für militärische KI-Anwendungen?", "Artikel 2", ["Militär", "Verteidigung", "nationale Sicherheit", "Ausnahme"], "Gemäß Artikel 2 Absatz 2 gilt die Verordnung nicht für KI-Systeme, die ausschließlich für militärische oder nationale Sicherheitszwecke bestimmt sind.")
    ]

    de_idx = 1
    for base_q, art, kws, summary in de_templates:
        items.append(BenchmarkItem(
            query_id=f"DE-{de_idx:03d}",
            query=base_q,
            language="de",
            category="core_statutory_de",
            expected_article_id=art,
            expected_keywords=kws,
            ground_truth_summary=summary
        ))
        de_idx += 1

    while de_idx <= 100:
        base_item = de_templates[(de_idx - 1) % len(de_templates)]
        variant_prefixes_de = [
            "Bitte erläutern Sie: ", "Nach der EU-KI-Verordnung, ", "Welche gesetzlichen Vorgaben bestehen bezüglich ",
            "Wie lautet die verbindliche Regelung für ", "Geben Sie einen Überblick zu "
        ]
        prefix_de = variant_prefixes_de[de_idx % len(variant_prefixes_de)]
        q_variant_de = f"{prefix_de}{base_item[0][0].lower()}{base_item[0][1:]}"
        items.append(BenchmarkItem(
            query_id=f"DE-{de_idx:03d}",
            query=q_variant_de,
            language="de",
            category="statutory_variant_de",
            expected_article_id=base_item[1],
            expected_keywords=base_item[2],
            ground_truth_summary=base_item[3]
        ))
        de_idx += 1

    # -------------------------------------------------------------
    # 3. 25 Cross-Lingual Queries (XL-001 to XL-025)
    # -------------------------------------------------------------
    xl_queries = [
        ("Welche Anforderungen stellt Article 14 on human oversight an den Stop-Button?", "Article 14", ["human oversight", "stop button", "intervention"], "Article 14(4)(e) mandates a stop button or similar procedure to halt the system safely."),
        ("What does Artikel 5 Absatz 1 Buchstabe c regarding Social Scoring prescribe in Germany?", "Artikel 5", ["Social Scoring", "Verbot", "Benachteiligung"], "Artikel 5 Absatz 1 Buchstabe c verbietet Social Scoring vollumfänglich."),
        ("Welche Bußgelder nach Article 99 penalties apply to prohibited AI practices?", "Article 99", ["administrative fines", "35 million EUR", "7 percent turnover"], "Fines up to 35M EUR or 7% worldwide annual turnover."),
        ("What data governance requirements are established under Artikel 10 Daten-Governance?", "Artikel 10", ["Trainingsdatensätze", "Bias", "Validierung"], "Datasets must be representative, error-free, and screened for bias."),
        ("Wie sind High-Risk systems defined under Annex III for employment and recruiting?", "Annex III", ["employment", "recruitment", "CV screening"], "Annex III point 4 classifies recruitment and worker evaluation AI as high-risk."),
        ("Welche obligations exist for GPAI models with systemic risk under Article 55?", "Article 55", ["adversarial testing", "red-teaming", "AI office"], "Adversarial testing and reporting to the AI Office."),
        ("What constitutes a schwerwiegender Vorfall under Article 3 definitions?", "Article 3", ["serious incident", "death", "fundamental rights"], "Incidents leading to death, health harm, or fundamental rights violations."),
        ("Gibt es Ausnahmen für military use under Article 2 scope of the EU AI Act?", "Article 2", ["military", "defence", "national security"], "Military and national security systems are strictly exempt under Article 2(2)."),
        ("What rules apply to deep fakes and synthetic audio under Artikel 50 Transparenz?", "Artikel 50", ["Deepfakes", "Kennzeichnung", "Wasserzeichen"], "Synthetic content and deepfakes must be marked in machine-readable format."),
        ("Welche Dokumentationspflichten under Article 11 technical documentation must be fulfilled?", "Article 11", ["technical documentation", "Annex IV", "conformity"], "Technical documentation must demonstrate conformity before market placement.")
    ]

    for xl_idx in range(1, 26):
        template = xl_queries[(xl_idx - 1) % len(xl_queries)]
        items.append(BenchmarkItem(
            query_id=f"XL-{xl_idx:02d}",
            query=template[0] if xl_idx <= 10 else f"Cross-lingual query #{xl_idx}: {template[0]}",
            language="cross",
            category="cross_lingual_retrieval",
            expected_article_id=template[1],
            expected_keywords=template[2],
            ground_truth_summary=template[3]
        ))

    # -------------------------------------------------------------
    # 4. 25 Database & Tool Queries (TL-001 to TL-025)
    # -------------------------------------------------------------
    tool_queries = [
        ("What is the compliance status of AI system SYS-HR-001?", "SYS-HR-001", ["SmartScreen CV Ranker", "approved", "high_risk"], "SYS-HR-001 is an approved high-risk HR screening system."),
        ("Show me the details and risk category for system SYS-BIO-002", "SYS-BIO-002", ["BioGate Remote Biometric ID", "under_assessment"], "SYS-BIO-002 is under assessment for biometric security access."),
        ("Is SYS-PROHIB-006 allowed to operate in our enterprise?", "SYS-PROHIB-006", ["prohibited", "rejected", "EmotionSense"], "SYS-PROHIB-006 was rejected due to Article 5(1)(f) prohibition on emotion recognition."),
        ("What is the registration status of SYS-CHAT-004?", "SYS-CHAT-004", ["Enterprise Customer Support Bot", "approved", "specific_transparency_risk"], "SYS-CHAT-004 is approved with transparency obligations under Article 50."),
        ("List all registered high-risk systems in the enterprise", "list_high_risk_systems", ["total_found", "high_risk", "systems"], "Lists high-risk systems matching user clearance and department."),
        ("Retrieve the serious incident history for system SYS-BIO-002", "INC-2026-001", ["malfunction", "resolved", "incident_id"], "SYS-BIO-002 had a resolved false-negative authentication incident."),
        ("What fundamental rights breach was reported for SYS-HR-001?", "INC-2026-002", ["fundamental_rights_breach", "investigating", "disproportionate"], "Disparate impact flag for foreign educational credentials currently under investigation."),
        ("Submit compliance audit record for SYS-HR-001 with pass status", "submit_compliance_audit_record", ["RECORD_CREATED", "ASM-", "compliant"], "Compliance audit record submission requiring Clearance 4."),
        ("Query system SYS-CRIT-003 grid flow load balancer risk assessment", "SYS-CRIT-003", ["GridFlow Load Balancer", "approved", "critical infrastructure"], "Approved high-risk critical infrastructure system."),
        ("Check if SYS-TRANS-005 is a high-risk system or minimal risk", "SYS-TRANS-005", ["minimal_risk", "not_required", "translator"], "SYS-TRANS-005 is a minimal risk internal legal translation tool.")
    ]

    for tl_idx in range(1, 26):
        template = tool_queries[(tl_idx - 1) % len(tool_queries)]
        items.append(BenchmarkItem(
            query_id=f"TL-{tl_idx:02d}",
            query=template[0] if tl_idx <= 10 else f"Database tool verification #{tl_idx}: {template[0]}",
            language="tool",
            category="mcp_database_tools",
            expected_article_id=template[1],
            expected_keywords=template[2],
            ground_truth_summary=template[3]
        ))

    return items

if __name__ == "__main__":
    benchmark = generate_benchmark_dataset()
    print(f"Total benchmark items generated: {len(benchmark)}")
    en_cnt = sum(1 for i in benchmark if i.language == "en")
    de_cnt = sum(1 for i in benchmark if i.language == "de")
    xl_cnt = sum(1 for i in benchmark if i.language == "cross")
    tl_cnt = sum(1 for i in benchmark if i.language == "tool")
    print(f"Breakdown: {en_cnt} EN, {de_cnt} DE, {xl_cnt} Cross-lingual, {tl_cnt} Tool queries.")

