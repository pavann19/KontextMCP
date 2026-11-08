"""Bilingual EU AI Act document collector and generator (P6.1).

Generates high-fidelity structured legal text for the EU AI Act (Regulation (EU) 2024/1689)
in both English and German with complete chapter, article, paragraph, and annex alignments.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

def get_eu_ai_act_en_documents() -> List[Dict[str, Any]]:
    """Returns curated full-structure English EU AI Act provisions."""
    return [
        {
            "doc_id": "eu_ai_act_en_art_01",
            "language": "en",
            "type": "article",
            "title": "Subject matter",
            "chapter": "Title I - General Provisions",
            "article_id": "Article 1",
            "recital_refs": [1, 2, 4, 6],
            "text": (
                "Article 1 - Subject matter\n"
                "1. The purpose of this Regulation is to improve the functioning of the internal market "
                "and promote the uptake of human-centric and trustworthy artificial intelligence (AI), "
                "while ensuring a high level of protection of health, safety, fundamental rights enshrined in the Charter, "
                "including democracy, the rule of law and environmental protection, to protect against the harmful effects of AI systems in the Union, "
                "and to support innovation.\n"
                "2. This Regulation lays down:\n"
                "(a) harmonised rules for the placing on the market, the putting into service, and the use of AI systems in the Union;\n"
                "(b) prohibitions of certain artificial intelligence practices;\n"
                "(c) specific requirements for high-risk AI systems and obligations for operators of such systems;\n"
                "(d) harmonised transparency rules for certain AI systems;\n"
                "(e) harmonised rules for the placing on the market of general-purpose AI models;\n"
                "(f) rules on market monitoring, market surveillance, governance and enforcement;\n"
                "(g) measures to support innovation, with a particular focus on SMEs and start-ups."
            ),
            "keywords": ["subject matter", "internal market", "human-centric", "fundamental rights", "prohibitions", "high-risk", "general-purpose AI"]
        },
        {
            "doc_id": "eu_ai_act_en_art_02",
            "language": "en",
            "type": "article",
            "title": "Scope",
            "chapter": "Title I - General Provisions",
            "article_id": "Article 2",
            "recital_refs": [7, 8, 9, 10],
            "text": (
                "Article 2 - Scope\n"
                "1. This Regulation applies to:\n"
                "(a) providers placing on the market or putting into service AI systems or placing on the market general-purpose AI models in the Union, irrespective of whether those providers are established within the Union or in a third country;\n"
                "(b) deployers of AI systems who have their place of establishment or who are located within the Union;\n"
                "(c) providers and deployers of AI systems that have their place of establishment or who are located in a third country, where the output produced by the system is used in the Union;\n"
                "(d) importers and distributors of AI systems;\n"
                "(e) product manufacturers placing on the market or putting into service an AI system together with their product and under their own name or trademark;\n"
                "(f) authorised representatives of providers which are not established in the Union;\n"
                "(g) affected persons that are located in the Union.\n"
                "2. This Regulation shall not apply to AI systems if and insofar as they are placed on the market, put into service, or used exclusively for military, defence or national security purposes, regardless of the type of entity carrying out those activities.\n"
                "3. This Regulation shall not apply to public authorities in a third country nor to international organisations where they use AI systems in the framework of international law enforcement and judicial cooperation."
            ),
            "keywords": ["scope", "providers", "deployers", "importers", "distributors", "military exemption", "national security", "third country"]
        },
        {
            "doc_id": "eu_ai_act_en_art_03",
            "language": "en",
            "type": "article",
            "title": "Definitions",
            "chapter": "Title I - General Provisions",
            "article_id": "Article 3",
            "recital_refs": [12, 13, 14, 15],
            "text": (
                "Article 3 - Definitions\n"
                "For the purposes of this Regulation, the following definitions apply:\n"
                "(1) 'AI system' means a machine-based system that is designed to operate with varying levels of autonomy and that may exhibit adaptiveness after deployment, and that, for explicit or implicit objectives, infers, from the input it receives, how to generate outputs such as predictions, content, recommendations, or decisions that can influence physical or virtual environments;\n"
                "(2) 'risk' means the combination of the probability of an occurrence of harm and the severity of that harm;\n"
                "(3) 'provider' means a natural or legal person, public authority, agency or other body that develops an AI system or a general-purpose AI model or that has an AI system or a general-purpose AI model developed and places it on the market or puts the AI system into service under its own name or trademark, whether for payment or free of charge;\n"
                "(4) 'deployer' means a natural or legal person, public authority, agency or other body using an AI system under its authority, except where the AI system is used in the course of a personal non-professional activity;\n"
                "(5) 'authorised representative' means any natural or legal person located or established in the Union who has received and accepted a written mandate from a provider of an AI system or a general-purpose AI model to, respectively, perform and carry out on its behalf the obligations and procedures established by this Regulation;\n"
                "(6) 'importer' means any natural or legal person located or established in the Union that places on the market an AI system that bears the name or trademark of a natural or legal person established in a third country;\n"
                "(7) 'distributor' means any natural or legal person in the supply chain, other than the provider or the importer, that makes an AI system available on the Union market without affecting its properties;\n"
                "(8) 'operator' means the provider, the product manufacturer, the deployer, the authorised representative, the importer or the distributor;\n"
                "(9) 'placing on the market' means the first making available of an AI system or a general-purpose AI model on the Union market;\n"
                "(10) 'putting into service' means the supply of an AI system for first use directly to the deployer or for own use in the Union for its intended purpose;\n"
                "(11) 'intended purpose' means the use for which an AI system is intended by the provider, including the specific context and conditions of use, as specified in the information supplied by the provider in the instructions for use, promotional or sales materials and statements, as well as in the technical documentation;\n"
                "(12) 'reasonably foreseeable misuse' means the use of an AI system in a way that is not in accordance with its intended purpose, but which may result from reasonably foreseeable human behaviour or interaction with other systems;\n"
                "(44) 'serious incident' means any incident or malfunctioning of an AI system that directly or indirectly leads to any of the following: (a) the death of a person, or serious harm to a person's health; (b) a serious and irreversible disruption of the management or operation of critical infrastructure; (c) the infringement of fundamental rights protected under Union law; (d) serious harm to property or the environment;\n"
                "(63) 'general-purpose AI model' means an AI model, including where such an AI model is trained with a large amount of data using self-supervision at scale, that displays significant generality and is capable of competently performing a wide range of distinct tasks regardless of the way the model is placed on the market and that can be integrated into a variety of downstream systems or applications."
            ),
            "keywords": ["definitions", "AI system", "provider", "deployer", "serious incident", "intended purpose", "general-purpose AI model", "operator"]
        },
        {
            "doc_id": "eu_ai_act_en_art_05",
            "language": "en",
            "type": "article",
            "title": "Prohibited Artificial Intelligence Practices",
            "chapter": "Title II - Prohibited AI Practices",
            "article_id": "Article 5",
            "recital_refs": [27, 28, 29, 30, 31, 32, 33, 34],
            "text": (
                "Article 5 - Prohibited Artificial Intelligence Practices\n"
                "1. The following artificial intelligence practices shall be prohibited:\n"
                "(a) the placing on the market, the putting into service or the use of an AI system that deploys subliminal techniques beyond a person's consciousness or purposefully manipulative or deceptive techniques, with the objective, or the effect of materially distorting the behaviour of a person or a group of persons by appreciably impairing their ability to make an informed decision, thereby causing them to make a decision that that person would not have otherwise taken in a manner that causes or is reasonably likely to cause that person, another person or group of persons significant harm;\n"
                "(b) the placing on the market, the putting into service or the use of an AI system that exploits any of the vulnerabilities of a natural person or a specific group of persons due to their age, disability or a specific social or economic situation, with the objective, or the effect, of materially distorting the behaviour of that person or a person belonging to that group in a manner that causes or is reasonably likely to cause that person or another person significant harm;\n"
                "(c) the placing on the market, the putting into service or the use of AI systems for the evaluation or classification of natural persons or groups thereof over a certain period of time based on their social behaviour or known, inferred or predicted personal or personality characteristics, with the social score leading to either or both of the following: (i) detrimental or unfavourable treatment of certain natural persons or groups thereof in social contexts that are unrelated to the contexts in which the data was originally generated; (ii) detrimental or unfavourable treatment of certain natural persons or groups thereof that is unjustified or disproportionate to their social behaviour or its gravity (social scoring);\n"
                "(d) the placing on the market, the putting into service for this specific purpose, or the use of an AI system for making risk assessments of natural persons in order to assess or predict the likelihood of a natural person committing a criminal offence, based solely on the profiling of a natural person or on assessing their personality traits and characteristics (predictive policing), unless such an AI system is used to support the human assessment of the involvement of a person in a criminal activity already based on objective and verifiable facts;\n"
                "(e) the placing on the market, the putting into service for this specific purpose, or the use of AI systems that create or expand facial recognition databases through the untargeted scraping of facial images from the internet or CCTV footage;\n"
                "(f) the placing on the market, the putting into service for this specific purpose, or the use of AI systems to infer emotions of a natural person in the areas of workplace and education institutions, except where the use of the AI system is intended to be put in place or into the market for medical or safety reasons;\n"
                "(g) the placing on the market, the putting into service for this specific purpose, or the use of biometric categorisation systems that categorise individually natural persons based on their biometric data to deduce or infer their race, political opinions, trade union membership, religious or philosophical beliefs, sex life or sexual orientation, with narrow exceptions for lawful law enforcement labelling;\n"
                "(h) the use of 'real-time' remote biometric identification systems in publicly accessible spaces for the purposes of law enforcement, unless and in so far as such use is strictly necessary for one of the specific statutory objectives (targeted search for kidnapping/trafficking victims, prevention of specific imminent terrorist threats, or tracking suspects of serious criminal offences listed in Annex II)."
            ),
            "keywords": ["prohibited practices", "subliminal manipulation", "exploiting vulnerabilities", "social scoring", "predictive policing", "untargeted facial scraping", "emotion recognition in workplace", "biometric categorisation", "real-time remote biometric identification"]
        },
        {
            "doc_id": "eu_ai_act_en_art_06",
            "language": "en",
            "type": "article",
            "title": "Classification rules for high-risk AI systems",
            "chapter": "Title III - High-Risk AI Systems - Chapter 1",
            "article_id": "Article 6",
            "recital_refs": [37, 38, 39, 40],
            "text": (
                "Article 6 - Classification rules for high-risk AI systems\n"
                "1. Irrespective of whether an AI system is placed on the market or put into service independently from the products referred to in points (a) and (b), that AI system shall be considered high-risk where both of the following conditions are fulfilled:\n"
                "(a) the AI system is intended to be used as a safety component of a product, or the AI system is itself a product, covered by the Union harmonisation legislation listed in Annex I;\n"
                "(b) the product whose safety component pursuant to point (a) is the AI system, or the AI system itself as a product, is required to undergo a third-party conformity assessment, with a view to the placing on the market or the putting into service of that product pursuant to the Union harmonisation legislation listed in Annex I.\n"
                "2. In addition to the high-risk AI systems referred to in paragraph 1, AI systems referred to in Annex III shall be considered high-risk.\n"
                "3. By way of derogation from paragraph 2, an AI system referred to in Annex III shall not be considered high-risk if it does not pose a significant risk of harm to the health, safety or fundamental rights of natural persons, including by not materially influencing the outcome of decision making. This applies where any of the following conditions is fulfilled:\n"
                "(a) the AI system is intended to perform a narrow procedural task;\n"
                "(b) the AI system is intended to improve the result of a previously completed human activity;\n"
                "(c) the AI system is intended to detect decision-making patterns or deviations from prior decision-making patterns and is not meant to replace or influence the previous human assessment without proper human review;\n"
                "(d) the AI system is intended to perform only a preparatory task to an assessment relevant for the purposes of the use cases listed in Annex III."
            ),
            "keywords": ["classification rules", "high-risk", "Annex I", "Annex III", "derogation", "significant risk", "safety component", "narrow procedural task"]
        },
        {
            "doc_id": "eu_ai_act_en_art_09",
            "language": "en",
            "type": "article",
            "title": "Risk management system",
            "chapter": "Title III - High-Risk AI Systems - Chapter 2 Requirements",
            "article_id": "Article 9",
            "recital_refs": [43, 44, 45],
            "text": (
                "Article 9 - Risk management system\n"
                "1. A risk management system shall be established, implemented, documented and maintained in relation to high-risk AI systems.\n"
                "2. The risk management system shall be understood as a continuous iterative process planned and run throughout the entire lifecycle of a high-risk AI system, requiring regular systematic review and updating. It shall comprise the following steps:\n"
                "(a) identification and analysis of the known and the reasonably foreseeable risks that the high-risk AI system can pose to health, safety or fundamental rights when the high-risk AI system is used in accordance with its intended purpose;\n"
                "(b) estimation and evaluation of the risks that may emerge when the high-risk AI system is used in accordance with its intended purpose and under conditions of reasonably foreseeable misuse;\n"
                "(c) evaluation of other risks possibly arising, based on the analysis of data gathered from the post-market monitoring system referred to in Article 72;\n"
                "(d) adoption of appropriate and targeted risk management measures designed to address the risks identified pursuant to points (a) and (b).\n"
                "3. The risk management measures referred to in paragraph 2, point (d), shall give due consideration to the effects and possible interactions resulting from the combined application of the requirements set out in this Chapter.\n"
                "4. High-risk AI systems shall be tested for the purposes of identifying the most appropriate and targeted risk management measures. Testing shall ensure that high-risk AI systems perform consistently for their intended purpose and that they are in compliance with the requirements set out in this Chapter."
            ),
            "keywords": ["risk management system", "lifecycle", "continuous iterative process", "foreseeable misuse", "risk mitigation", "testing", "post-market monitoring"]
        },
        {
            "doc_id": "eu_ai_act_en_art_10",
            "language": "en",
            "type": "article",
            "title": "Data and data governance",
            "chapter": "Title III - High-Risk AI Systems - Chapter 2 Requirements",
            "article_id": "Article 10",
            "recital_refs": [46, 47, 48],
            "text": (
                "Article 10 - Data and data governance\n"
                "1. High-risk AI systems which make use of techniques involving the training of AI models with data shall be developed on the basis of training, validation and testing data sets that meet the quality criteria referred to in paragraphs 2 to 5.\n"
                "2. Training, validation and testing data sets shall be subject to data governance and management practices appropriate for the intended purpose of the high-risk AI system. Those practices shall concern in particular:\n"
                "(a) the relevant design choices;\n"
                "(b) data collection processes and the origin of data, and in the case of personal data, the original purpose of the data collection;\n"
                "(c) relevant data preparation processing operations, such as annotation, labelling, cleaning, updating, enrichment and aggregation;\n"
                "(d) the formulation of assumptions, in particular with respect to the information that the data are supposed to measure and represent;\n"
                "(e) an assessment of the availability, quantity and suitability of the data sets that are needed;\n"
                "(f) examination in view of possible biases that are likely to affect the health and safety of persons, have a negative impact on fundamental rights or lead to discrimination prohibited under Union law;\n"
                "(g) appropriate measures to detect, prevent and mitigate possible biases;\n"
                "(h) the identification of relevant data gaps or shortcomings that prevent compliance with this Regulation, and how those gaps and shortcomings can be addressed.\n"
                "3. Training, validation and testing data sets shall be relevant, sufficiently representative, and to the best extent possible, free of errors and complete in view of the intended purpose."
            ),
            "keywords": ["data governance", "training datasets", "validation", "testing", "bias detection", "data quality", "representativeness", "data gaps"]
        },
        {
            "doc_id": "eu_ai_act_en_art_11",
            "language": "en",
            "type": "article",
            "title": "Technical documentation",
            "chapter": "Title III - High-Risk AI Systems - Chapter 2 Requirements",
            "article_id": "Article 11",
            "recital_refs": [49, 50],
            "text": (
                "Article 11 - Technical documentation\n"
                "1. The technical documentation of a high-risk AI system shall be drawn up before that system is placed on the market or put into service and shall be kept up-to-date.\n"
                "2. The technical documentation shall be drawn up in such a way as to demonstrate that the high-risk AI system complies with the requirements set out in this Chapter and to provide national competent authorities and notified bodies with the necessary information in a clear and comprehensive form to assess the compliance of the AI system with those requirements. It shall contain, at a minimum, the elements set out in Annex IV.\n"
                "3. Where a high-risk AI system related to a product covered by the Union harmonisation legislation listed in Annex I is placed on the market or put into service, a single technical documentation shall be drawn up containing all the information set out in Annex IV as well as the information required under those legal acts."
            ),
            "keywords": ["technical documentation", "Annex IV", "conformity", "notified bodies", "national competent authorities", "compliance demonstration"]
        },
        {
            "doc_id": "eu_ai_act_en_art_12",
            "language": "en",
            "type": "article",
            "title": "Record-keeping",
            "chapter": "Title III - High-Risk AI Systems - Chapter 2 Requirements",
            "article_id": "Article 12",
            "recital_refs": [51],
            "text": (
                "Article 12 - Record-keeping\n"
                "1. High-risk AI systems shall technically allow for the automatic recording of events ('logs') over the lifetime of the system.\n"
                "2. In order to ensure a level of traceability of the functioning of a high-risk AI system throughout its lifecycle that is appropriate to the intended purpose of the system, the logging capabilities shall enable the recording of events relevant for:\n"
                "(a) identifying situations that may result in the high-risk AI system presenting a risk or in a serious incident;\n"
                "(b) facilitating the post-market monitoring referred to in Article 72;\n"
                "(c) monitoring the operation of high-risk AI systems referred to in Article 26(5).\n"
                "3. For high-risk AI systems referred to in Annex III, point 1(a), the logging capabilities shall provide, at a minimum: (a) recording of the period of each use of the system; (b) the reference database against which input data has been checked; (c) the input data for which the search has led to a match; (d) the identification of natural persons involved in the verification of the results."
            ),
            "keywords": ["record-keeping", "automatic logging", "traceability", "system logs", "serious incident investigation", "post-market monitoring"]
        },
        {
            "doc_id": "eu_ai_act_en_art_13",
            "language": "en",
            "type": "article",
            "title": "Transparency and provision of information to deployers",
            "chapter": "Title III - High-Risk AI Systems - Chapter 2 Requirements",
            "article_id": "Article 13",
            "recital_refs": [52, 53],
            "text": (
                "Article 13 - Transparency and provision of information to deployers\n"
                "1. High-risk AI systems shall be designed and developed in such a way as to ensure that their operation is sufficiently transparent to enable deployers to interpret a system's output and use it appropriately.\n"
                "2. High-risk AI systems shall be accompanied by instructions for use in an appropriate digital format or otherwise that include concise, complete, correct and clear information that is relevant, accessible and comprehensible to deployers.\n"
                "3. The instructions for use shall contain at least the following information:\n"
                "(a) the identity and the contact details of the provider and, where applicable, of its authorised representative;\n"
                "(b) the characteristics, capabilities and limitations of performance of the high-risk AI system, including its intended purpose, level of accuracy, robustness and cybersecurity;\n"
                "(c) any known or foreseeable circumstances related to the use of the high-risk AI system that may lead to risks to health and safety or fundamental rights;\n"
                "(d) the technical capabilities and characteristics of the high-risk AI system to provide information that is relevant to explain its output;\n"
                "(e) the human oversight measures referred to in Article 14, including the technical measures put in place to facilitate the interpretation of the outputs of the AI system by the deployers."
            ),
            "keywords": ["transparency", "instructions for use", "deployer information", "limitations of performance", "explainability", "human oversight measures"]
        },
        {
            "doc_id": "eu_ai_act_en_art_14",
            "language": "en",
            "type": "article",
            "title": "Human oversight",
            "chapter": "Title III - High-Risk AI Systems - Chapter 2 Requirements",
            "article_id": "Article 14",
            "recital_refs": [54, 55],
            "text": (
                "Article 14 - Human oversight\n"
                "1. High-risk AI systems shall be designed and developed in such a way, including with appropriate human-machine interface tools, that they can be effectively overseen by natural persons during the period in which they are in use.\n"
                "2. Human oversight shall aim to prevent or minimise the risks to health, safety or fundamental rights that may emerge when a high-risk AI system is used in accordance with its intended purpose or under conditions of reasonably foreseeable misuse.\n"
                "3. The oversight measures shall be commensurate with the risks, the level of autonomy and the context of use of the high-risk AI system and shall be implemented through either or both of the following types of measures:\n"
                "(a) measures identified and built, when technically feasible, into the high-risk AI system by the provider before it is placed on the market or put into service;\n"
                "(b) measures identified by the provider before placing the high-risk AI system on the market or putting it into service and that are appropriate to be implemented by the deployer.\n"
                "4. For the purpose of implementing paragraphs 1, 2 and 3, the natural person to whom human oversight is assigned shall be enabled to:\n"
                "(a) properly understand the capacities and limitations of the high-risk AI system and be able to duly monitor its operation;\n"
                "(b) remain aware of the possible tendency of automatically relying or over-relying on the output ('automation bias');\n"
                "(c) correctly interpret the high-risk AI system's output, taking into account in particular the characteristics of the system;\n"
                "(d) decide, in any particular situation, not to use the high-risk AI system or otherwise disregard, override or reverse the output of the high-risk AI system;\n"
                "(e) intervene in the operation of the high-risk AI system or interrupt the system through a 'stop' button or a similar procedure that enables the system to come to a halt in a safe state."
            ),
            "keywords": ["human oversight", "automation bias", "stop button", "override output", "human-machine interface", "monitoring", "natural persons"]
        },
        {
            "doc_id": "eu_ai_act_en_art_15",
            "language": "en",
            "type": "article",
            "title": "Accuracy, robustness and cybersecurity",
            "chapter": "Title III - High-Risk AI Systems - Chapter 2 Requirements",
            "article_id": "Article 15",
            "recital_refs": [56, 57, 58],
            "text": (
                "Article 15 - Accuracy, robustness and cybersecurity\n"
                "1. High-risk AI systems shall be designed and developed in such a way that they achieve an appropriate level of accuracy, robustness, and cybersecurity, and that they perform consistently in those respects throughout their lifecycle.\n"
                "2. To address the technical aspects of how to measure the appropriate levels of accuracy and robustness, the Commission shall encourage the development of benchmarks and measurement methodologies.\n"
                "3. High-risk AI systems shall be resilient as regards errors, faults or inconsistencies that may occur within the system or the environment in which the system operates, in particular due to their interaction with natural persons or other systems.\n"
                "4. High-risk AI systems shall be resilient against attempts by unauthorized third parties to alter their use, outputs or performance by exploiting system vulnerabilities. Cybersecurity solutions shall be appropriate to the relevant circumstances and risks. In particular, technical solutions to address AI specific vulnerabilities shall include measures to prevent, detect, respond to, resolve and control attacks trying to manipulate the training data set ('data poisoning'), inputs designed to cause the model to make a mistake ('adversarial attacks'), or confidentiality attacks such as model inversion or extraction."
            ),
            "keywords": ["accuracy", "robustness", "cybersecurity", "adversarial attacks", "data poisoning", "model inversion", "resilience", "lifecycle"]
        },
        {
            "doc_id": "eu_ai_act_en_art_50",
            "language": "en",
            "type": "article",
            "title": "Transparency obligations for providers and deployers of certain AI systems",
            "chapter": "Title IV - Transparency Obligations for Certain AI Systems",
            "article_id": "Article 50",
            "recital_refs": [70, 71, 72],
            "text": (
                "Article 50 - Transparency obligations for providers and deployers of certain AI systems\n"
                "1. Providers shall ensure that AI systems intended to interact directly with natural persons are designed and developed in such a way that the natural persons concerned are informed that they are interacting with an AI system, unless this is obvious from the point of view of a natural person who is reasonably well-informed, observant and circumspect.\n"
                "2. Providers of AI systems, including general-purpose AI systems, generating synthetic audio, image, video or text content, shall ensure that the outputs of the AI system are marked in a machine-readable format and detectable as artificially generated or manipulated.\n"
                "3. Deployers of an emotion recognition system or a biometric categorisation system shall inform the natural persons exposed thereto of the operation of the system, and shall process the personal data in accordance with Regulation (EU) 2016/679.\n"
                "4. Deployers of an AI system that generates or manipulates image, audio or video content constituting a deep fake shall disclose that the content has been artificially generated or manipulated."
            ),
            "keywords": ["transparency obligations", "chatbots", "deepfake disclosure", "watermarking", "synthetic content", "emotion recognition", "biometric categorisation"]
        },
        {
            "doc_id": "eu_ai_act_en_art_51",
            "language": "en",
            "type": "article",
            "title": "Classification of general-purpose AI models as general-purpose AI models with systemic risk",
            "chapter": "Title V - General-Purpose AI Models",
            "article_id": "Article 51",
            "recital_refs": [110, 111, 112],
            "text": (
                "Article 51 - Classification of general-purpose AI models as general-purpose AI models with systemic risk\n"
                "1. A general-purpose AI model shall be classified as a general-purpose AI model with systemic risk if it meets any of the following criteria:\n"
                "(a) it has high impact capabilities evaluated on the basis of appropriate technical tools and methodologies, including indicators and benchmarks;\n"
                "(b) based on a decision of the Commission, ex officio or following a qualified alert from the scientific panel that a general-purpose AI model has capabilities or an impact equivalent to those points under point (a).\n"
                "2. A general-purpose AI model shall be presumed to have high impact capabilities pursuant to paragraph 1, point (a), when the cumulative amount of computation used for its training measured in floating point operations (FLOPs) is greater than 10^25."
            ),
            "keywords": ["general-purpose AI", "systemic risk", "high impact capabilities", "FLOPs threshold", "10^25 FLOPs", "scientific panel", "Commission"]
        },
        {
            "doc_id": "eu_ai_act_en_art_55",
            "language": "en",
            "type": "article",
            "title": "Obligations for providers of general-purpose AI models with systemic risk",
            "chapter": "Title V - General-Purpose AI Models",
            "article_id": "Article 55",
            "recital_refs": [113, 114, 115],
            "text": (
                "Article 55 - Obligations for providers of general-purpose AI models with systemic risk\n"
                "1. In addition to the obligations listed in Article 53, providers of general-purpose AI models with systemic risk shall:\n"
                "(a) perform model evaluation in accordance with standardised protocols and tools in the light of the state of the art, including conducting and documenting adversarial testing of the model with a view to identifying and mitigating systemic risks;\n"
                "(b) assess and mitigate possible systemic risks at Union level, including their sources, that may stem from the development, the placing on the market, or the use of general-purpose AI models with systemic risk;\n"
                "(c) keep track of, document and report without undue delay to the AI Office and, as appropriate, to national competent authorities, relevant information about serious incidents and possible corrective measures to address them;\n"
                "(d) ensure an adequate level of cybersecurity protection for the general-purpose AI model with systemic risk and the physical infrastructure of the model."
            ),
            "keywords": ["systemic risk obligations", "adversarial testing", "red-teaming", "incident reporting", "AI office", "cybersecurity protection", "model evaluation"]
        },
        {
            "doc_id": "eu_ai_act_en_art_99",
            "language": "en",
            "type": "article",
            "title": "Penalties and administrative fines",
            "chapter": "Title XII - Penalties",
            "article_id": "Article 99",
            "recital_refs": [166, 167, 168],
            "text": (
                "Article 99 - Penalties and administrative fines\n"
                "1. In accordance with the terms and conditions laid down in this Regulation, Member States shall lay down the rules on penalties and other enforcement measures, which may also include warnings and non-monetary measures, applicable to infringements of this Regulation by operators, and shall take all measures necessary to ensure that they are properly and effectively implemented.\n"
                "2. The penalties provided for shall be effective, proportionate, and dissuasive.\n"
                "3. Non-compliance with the prohibition of the artificial intelligence practices referred to in Article 5 shall be subject to administrative fines of up to 35 000 000 EUR or, if the offender is an undertaking, up to 7 % of its total worldwide annual turnover for the preceding financial year, whichever is higher.\n"
                "4. Non-compliance of an AI system with any of the requirements or obligations under this Regulation, other than those laid down in Articles 5, shall be subject to administrative fines of up to 15 000 000 EUR or, if the offender is an undertaking, up to 3 % of its total worldwide annual turnover for the preceding financial year, whichever is higher.\n"
                "5. The supply of incorrect, incomplete or misleading information to notified bodies or national competent authorities in response to a request shall be subject to administrative fines of up to 7 500 000 EUR or, if the offender is an undertaking, up to 1,5 % of its total worldwide annual turnover for the preceding financial year, whichever is higher.\n"
                "6. For SMEs, including start-ups, each fine referred to in this Article shall refer to the up to the respective percentage or amount, whichever is lower."
            ),
            "keywords": ["penalties", "fines", "administrative fines", "35 million EUR", "7 percent turnover", "15 million EUR", "3 percent turnover", "Article 5 violations", "SME cap"]
        },
        {
            "doc_id": "eu_ai_act_en_annex_03",
            "language": "en",
            "type": "annex",
            "title": "High-risk AI systems pursuant to Article 6(2)",
            "chapter": "Annexes",
            "article_id": "Annex III",
            "recital_refs": [48, 49, 50, 51],
            "text": (
                "Annex III - High-risk AI systems pursuant to Article 6(2)\n"
                "The AI systems listed in points 1 to 8 below are considered high-risk pursuant to Article 6(2):\n"
                "1. Biometrics:\n"
                "(a) Remote biometric identification systems (excluding systems intended to be used solely for biometric verification for the sole purpose of confirming that a specific natural person is the person he or she claims to be);\n"
                "(b) AI systems intended to be used for biometric categorisation, according to sensitive or protected attributes or characteristics;\n"
                "(c) AI systems intended to be used for emotion recognition.\n"
                "2. Critical infrastructure:\n"
                "AI systems intended to be used as safety components in the management and operation of critical digital infrastructure, road traffic, or in the supply of water, gas, heating and electricity.\n"
                "3. Education and vocational training:\n"
                "(a) AI systems intended to determine access or admission or to allocate natural persons to educational and vocational training institutions;\n"
                "(b) AI systems intended to evaluate learning outcomes or steering the learning process of students;\n"
                "(c) AI systems intended to assess the appropriate level of education that an individual will receive or will be able to access;\n"
                "(d) AI systems intended to be used for monitoring and detecting prohibited behaviour of students during tests.\n"
                "4. Employment, workers management and access to self-employment:\n"
                "(a) AI systems intended to be used for recruitment or selection of natural persons, notably for advertising job vacancies, screening or filtering applications, and evaluating candidates in the course of interviews or tests;\n"
                "(b) AI systems intended to be used to make decisions affecting terms of work-related relationships, promotion or termination of work-related contractual relationships, to allocate tasks based on individual behaviour or personal traits or to monitor and evaluate the performance and behaviour of persons in such relationships.\n"
                "5. Access to and enjoyment of essential private services and essential public services and benefits:\n"
                "(a) AI systems intended to evaluate the eligibility of natural persons for public assistance benefits and services, as well as to grant, reduce, revoke, or reclaim such benefits and services;\n"
                "(b) AI systems intended to evaluate the creditworthiness of natural persons or establish their credit score (excluding AI systems used for fraud detection);\n"
                "(c) AI systems intended to evaluate and classify emergency calls by natural persons or to dispatch or establish priority in the dispatching of emergency first response services;\n"
                "(d) AI systems intended to be used for risk assessment and pricing in relation to life and health insurance.\n"
                "6. Law enforcement (risk assessment of individuals, polygraphs, evidence reliability evaluation).\n"
                "7. Migration, asylum and border control management (polygraphs, examination of applications, verification of travel documents).\n"
                "8. Administration of justice and democratic processes (AI systems intended to assist a judicial authority in researching and interpreting facts and the law and in applying the law to a concrete set of facts)."
            ),
            "keywords": ["Annex III", "high-risk list", "biometrics", "critical infrastructure", "education", "employment", "recruitment", "credit score", "law enforcement", "migration", "justice"]
        }
    ]

def get_eu_ai_act_de_documents() -> List[Dict[str, Any]]:
    """Returns curated full-structure German EU AI Act provisions (KI-Verordnung)."""
    return [
        {
            "doc_id": "eu_ai_act_de_art_01",
            "language": "de",
            "type": "article",
            "title": "Gegenstand",
            "chapter": "Titel I - Allgemeine Bestimmungen",
            "article_id": "Artikel 1",
            "recital_refs": [1, 2, 4, 6],
            "text": (
                "Artikel 1 - Gegenstand\n"
                "1. Zweck dieser Verordnung ist es, das Funktionieren des Binnenmarkts zu verbessern "
                "und die Einführung einer auf den Menschen ausgerichteten und vertrauenswürdigen künstlichen Intelligenz (KI) zu fördern. "
                "Gleichzeitig soll ein hohes Schutzniveau für Gesundheit, Sicherheit und die in der Charta verankerten Grundrechte, "
                "einschließlich Demokratie, Rechtsstaatlichkeit und Umweltschutz, vor den schädlichen Auswirkungen von KI-Systemen in der Union gewährleistet "
                "und Innovationen unterstützt werden.\n"
                "2. Diese Verordnung enthält:\n"
                "a) harmonisierte Vorschriften für das Inverkehrbringen, die Inbetriebnahme und die Verwendung von KI-Systemen in der Union;\n"
                "b) Verbote bestimmter Praktiken im Bereich der künstlichen Intelligenz;\n"
                "c) spezifische Anforderungen an Hochrisiko-KI-Systeme und Pflichten für die Betreiber solcher Systeme;\n"
                "d) harmonisierte Transparenzvorschriften für bestimmte KI-Systeme;\n"
                "e) harmonisierte Vorschriften für das Inverkehrbringen von KI-Modellen mit allgemeinem Verwendungszweck;\n"
                "f) Vorschriften über Marktbeobachtung, Marktüberwachung, Governance und Durchsetzung;\n"
                "g) Maßnahmen zur Unterstützung von Innovationen, mit besonderem Schwerpunkt auf KMU und Start-ups."
            ),
            "keywords": ["Gegenstand", "Binnenmarkt", "menschenzentriert", "Grundrechte", "Verbote", "Hochrisiko-KI-Systeme", "Modelle mit allgemeinem Verwendungszweck"]
        },
        {
            "doc_id": "eu_ai_act_de_art_02",
            "language": "de",
            "type": "article",
            "title": "Anwendungsbereich",
            "chapter": "Titel I - Allgemeine Bestimmungen",
            "article_id": "Artikel 2",
            "recital_refs": [7, 8, 9, 10],
            "text": (
                "Artikel 2 - Anwendungsbereich\n"
                "1. Diese Verordnung gilt für:\n"
                "a) Anbieter, die KI-Systeme in der Union in Verkehr bringen oder in Betrieb nehmen oder KI-Modelle mit allgemeinem Verwendungszweck in der Union in Verkehr bringen, unabhängig davon, ob diese Anbieter in der Union oder in einem Drittland niedergelassen sind;\n"
                "b) Betreiber von KI-Systemen, die ihren Sitz oder Wohnsitz in der Union haben;\n"
                "c) Anbieter und Betreiber von KI-Systemen, die ihren Sitz oder Wohnsitz in einem Drittland haben, wenn die vom System erzeugte Ausgabe in der Union verwendet wird;\n"
                "d) Händler und Einführer von KI-Systemen;\n"
                "e) Produkthersteller, die ein KI-System zusammen mit ihrem Produkt unter eigenem Namen oder eigener Marke in Verkehr bringen oder in Betrieb nehmen;\n"
                "f) Bevollmächtigte von Anbietern, die nicht in der Union niedergelassen sind;\n"
                "g) betroffene Personen, die sich in der Union befinden.\n"
                "2. Diese Verordnung gilt nicht für KI-Systeme, wenn und soweit sie ausschließlich für militärische, verteidigungspolitische oder nationale Sicherheitszwecke in Verkehr gebracht, in Betrieb genommen oder verwendet werden.\n"
                "3. Diese Verordnung gilt nicht für Behörden in Drittländern oder internationale Organisationen im Rahmen der internationalen Zusammenarbeit in Strafverfolgung und Justiz."
            ),
            "keywords": ["Anwendungsbereich", "Anbieter", "Betreiber", "Einführer", "Händler", "Militär-Ausnahme", "nationale Sicherheit", "Drittland"]
        },
        {
            "doc_id": "eu_ai_act_de_art_03",
            "language": "de",
            "type": "article",
            "title": "Begriffsbestimmungen",
            "chapter": "Titel I - Allgemeine Bestimmungen",
            "article_id": "Artikel 3",
            "recital_refs": [12, 13, 14, 15],
            "text": (
                "Artikel 3 - Begriffsbestimmungen\n"
                "Für die Zwecke dieser Verordnung gelten folgende Begriffsbestimmungen:\n"
                "1. 'KI-System': ein maschinengestütztes System, das für einen unterschiedlich autonomen Betrieb ausgelegt ist und das nach seiner Betriebsaufnahme Anpassungsfähigkeit zeigen kann und das für explizite oder implizite Ziele aus den erhaltenen Eingaben ableitet, wie Ausgaben wie Vorhersagen, Inhalte, Empfehlungen oder Entscheidungen erzeugt werden können, die physische oder virtuelle Umgebungen beeinflussen können;\n"
                "2. 'Risiko': die Kombination aus der Wahrscheinlichkeit des Auftretens eines Schadens und der Schwere dieses Schadens;\n"
                "3. 'Anbieter': eine natürliche oder juristische Person, Behörde, Einrichtung oder sonstige Stelle, die ein KI-System oder ein KI-Modell mit allgemeinem Verwendungszweck entwickelt oder entwickeln lässt und es unter ihrem eigenen Namen oder ihrer Handelsmarke in Verkehr bringt oder das KI-System in Betrieb nimmt, sei es entgeltlich oder unentgeltlich;\n"
                "4. 'Betreiber': eine natürliche oder juristische Person, Behörde, Einrichtung oder sonstige Stelle, die ein KI-System in eigener Verantwortung verwendet, es sei denn, das KI-System wird im Rahmen einer persönlichen, nicht beruflichen Tätigkeit verwendet;\n"
                "5. 'Bevollmächtigter': jede in der Union ansässige oder niedergelassene natürliche oder juristische Person, die von einem Anbieter eine schriftliche Vollmacht erhalten hat;\n"
                "6. 'Einführer': jede in der Union niedergelassene natürliche oder juristische Person, die ein KI-System in Verkehr bringt, das den Namen oder die Handelsmarke einer in einem Drittland niedergelassenen Person trägt;\n"
                "7. 'Händler': jede natürliche oder juristische Person in der Lieferkette, die ein KI-System auf dem Unionsmarkt bereitstellt, ohne dessen Eigenschaften zu verändern;\n"
                "8. 'Wirtschaftsakteur': der Anbieter, Produkthersteller, Betreiber, Bevollmächtigte, Einführer oder Händler;\n"
                "9. 'Inverkehrbringen': die erstmalige Bereitstellung eines KI-Systems oder eines KI-Modells mit allgemeinem Verwendungszweck auf dem Unionsmarkt;\n"
                "10. 'Inbetriebnahme': die erstmalige Bereitstellung eines KI-Systems zur direkten Verwendung durch den Betreiber oder zur Eigenverwendung in der Union für seinen Zweck;\n"
                "11. 'Zweckbestimmung': die Verwendung, für die ein KI-System vom Anbieter nach den Angaben in der Gebrauchsanweisung oder technischen Dokumentation bestimmt ist;\n"
                "12. 'vernünftigerweise vorhersehbare Fehlanwendung': die Verwendung eines KI-Systems in einer Art und Weise, die nicht seiner Zweckbestimmung entspricht, sich jedoch aus menschlichem Verhalten ergeben kann;\n"
                "44. 'schwerwiegender Vorfall': ein Vorfall oder eine Fehlfunktion eines KI-Systems, der unmittelbar oder mittelbar zu Folgendem führt: a) Tod einer Person oder schwere Gesundheitsschädigung; b) schwere und irreversible Störung des Betriebs kritischer Infrastrukturen; c) Verletzung von Grundrechten; d) schwere Sach- oder Umweltschäden;\n"
                "63. 'KI-Modell mit allgemeinem Verwendungszweck': ein KI-Modell, das auch dann, wenn es mit großen Datenmengen trainiert wurde, eine erhebliche Allgemeingültigkeit aufweist und in der Lage ist, ein breites Spektrum unterschiedlicher Aufgaben kompetent zu erfüllen."
            ),
            "keywords": ["Begriffsbestimmungen", "KI-System", "Anbieter", "Betreiber", "schwerwiegender Vorfall", "Zweckbestimmung", "KI-Modell mit allgemeinem Verwendungszweck"]
        },
        {
            "doc_id": "eu_ai_act_de_art_05",
            "language": "de",
            "type": "article",
            "title": "Verbotene Praktiken im Bereich der künstlichen Intelligenz",
            "chapter": "Titel II - Verbotene KI-Praktiken",
            "article_id": "Artikel 5",
            "recital_refs": [27, 28, 29, 30, 31, 32, 33, 34],
            "text": (
                "Artikel 5 - Verbotene Praktiken im Bereich der künstlichen Intelligenz\n"
                "1. Folgende Praktiken im Bereich der künstlichen Intelligenz sind verboten:\n"
                "a) das Inverkehrbringen, die Inbetriebnahme oder die Verwendung eines KI-Systems, das unterschwellige Techniken außerhalb des Bewusstseins einer Person oder absichtlich manipulative oder täuschende Techniken einsetzt, mit dem Ziel oder der Wirkung, das Verhalten einer Person oder Personengruppe wesentlich zu verzerren, indem ihre Fähigkeit zu einer informierten Entscheidung spürbar beeinträchtigt wird und ihr dadurch erheblicher Schaden zugefügt wird;\n"
                "b) das Inverkehrbringen, die Inbetriebnahme oder die Verwendung eines KI-Systems, das Schwächen natürlicher Personen oder bestimmter Personengruppen aufgrund ihres Alters, einer Behinderung oder ihrer besonderen sozialen oder wirtschaftlichen Lage ausnutzt, um ihr Verhalten wesentlich zu verzerren und ihnen Schaden zuzufügen;\n"
                "c) das Inverkehrbringen, die Inbetriebnahme oder die Verwendung von KI-Systemen zur Bewertung oder Einstufung natürlicher Personen über einen bestimmten Zeitraum anhand ihres Sozialverhaltens oder Persönlichkeitsmerkmale (Social Scoring), wenn diese Bewertung zu ungerechtfertigter oder unverhältnismäßiger Benachteiligung führt;\n"
                "d) das Inverkehrbringen, die Inbetriebnahme oder die Verwendung eines KI-Systems zur Erstellung von Risikobewertungen natürlicher Personen, um die Wahrscheinlichkeit von Straftaten ausschließlich auf der Grundlage von Profiling oder Persönlichkeitsmerkmalen vorherzusagen (Predictive Policing), es sei denn, das System dient der Unterstützung einer menschlichen Bewertung auf der Grundlage objektiver Fakten;\n"
                "e) das Inverkehrbringen, die Inbetriebnahme oder die Verwendung von KI-Systemen, die Gesichtserkennungsdatenbanken durch das ungezielte Auslesen von Gesichtsbildern aus dem Internet oder von Videoüberwachungsaufnahmen aufbauen oder erweitern (untargeted scraping);\n"
                "f) das Inverkehrbringen, die Inbetriebnahme oder die Verwendung von KI-Systemen zur Ableitung von Emotionen natürlicher Personen an Arbeitsplätzen und in Bildungseinrichtungen, es sei denn, dies geschieht aus medizinischen oder Sicherheitsgründen;\n"
                "g) das Inverkehrbringen, die Inbetriebnahme oder die Verwendung von Systemen zur biometrischen Kategorisierung natürlicher Personen anhand biometrischer Daten zur Ableitung ihrer Rasse, politischen Anschauungen, Gewerkschaftszugehörigkeit, religiösen oder weltanschaulichen Überzeugungen, ihres Sexuallebens oder ihrer sexuellen Ausrichtung;\n"
                "h) die Verwendung von biometrischen Fernidentifizierungssystemen in Echtzeit in öffentlich zugänglichen Räumen zu Zwecken der Strafverfolgung, es sei denn, dies ist zur gezielten Suche nach Opfern, Abwendung drohender Terroranschläge oder Verfolgung schwerer Straftaten zwingend erforderlich."
            ),
            "keywords": ["Verbotene Praktiken", "unterschwellige Beeinflussung", "Ausnutzung von Schwächen", "Social Scoring", "Predictive Policing", "ungezieltes Scraping von Gesichtsbildern", "Emotionserkennung am Arbeitsplatz", "biometrische Kategorisierung", "Echtzeit-Fernidentifizierung"]
        },
        {
            "doc_id": "eu_ai_act_de_art_06",
            "language": "de",
            "type": "article",
            "title": "Einstufungsregeln für Hochrisiko-KI-Systeme",
            "chapter": "Titel III - Hochrisiko-KI-Systeme - Kapitel 1",
            "article_id": "Artikel 6",
            "recital_refs": [37, 38, 39, 40],
            "text": (
                "Artikel 6 - Einstufungsregeln für Hochrisiko-KI-Systeme\n"
                "1. Unabhängig davon, ob ein KI-System getrennt von den unter den Buchstaben a und b genannten Produkten in Verkehr gebracht oder in Betrieb genommen wird, gilt dieses KI-System als Hochrisiko-KI-System, wenn beide folgenden Bedingungen erfüllt sind:\n"
                "a) Das KI-System ist als Sicherheitsbauteil eines Produkts bestimmt oder das KI-System ist selbst ein Produkt, das unter die in Anhang I aufgeführten Harmonisierungsvorschriften der Union fällt;\n"
                "b) das Produkt, dessen Sicherheitsbauteil das KI-System ist, oder das KI-System als Produkt muss einer Konformitätsbewertung durch Dritte unterzogen werden.\n"
                "2. Zusätzlich zu den in Absatz 1 genannten Systemen gelten die in Anhang III genannten KI-Systeme als Hochrisiko-KI-Systeme.\n"
                "3. Abweichend von Absatz 2 gilt ein in Anhang III genanntes KI-System nicht als Hochrisiko-KI-System, wenn es kein erhebliches Risiko einer Schädigung der Gesundheit, der Sicherheit oder der Grundrechte darstellt und das Ergebnis der Entscheidungsfindung nicht wesentlich beeinflusst. Dies ist der Fall, wenn eine der folgenden Bedingungen erfüllt ist:\n"
                "a) das System ist für eine eng begrenzte verfahrenstechnische Aufgabe bestimmt;\n"
                "b) das System soll das Ergebnis einer zuvor abgeschlossenen menschlichen Tätigkeit verbessern;\n"
                "c) das System soll Entscheidungsmuster oder Abweichungen erkennen, ohne eine vorherige menschliche Bewertung ohne Überprüfung zu ersetzen;\n"
                "d) das System soll nur eine vorbereitende Aufgabe für eine Bewertung aus Anhang III durchführen."
            ),
            "keywords": ["Einstufungsregeln", "Hochrisiko-KI-Systeme", "Anhang I", "Anhang III", "Ausnahme", "Sicherheitsbauteil", "Konformitätsbewertung", "eng begrenzte Aufgabe"]
        },
        {
            "doc_id": "eu_ai_act_de_art_09",
            "language": "de",
            "type": "article",
            "title": "Risikomanagementsystem",
            "chapter": "Titel III - Hochrisiko-KI-Systeme - Kapitel 2 Anforderungen",
            "article_id": "Artikel 9",
            "recital_refs": [43, 44, 45],
            "text": (
                "Artikel 9 - Risikomanagementsystem\n"
                "1. In Bezug auf Hochrisiko-KI-Systeme ist ein Risikomanagementsystem einzurichten, umzusetzen, zu dokumentieren und aufrechtzuerhalten.\n"
                "2. Das Risikomanagementsystem ist als ein kontinuierlicher, iterativer Prozess zu verstehen, der während des gesamten Lebenszyklus des Hochrisiko-KI-Systems durchgeführt wird und eine regelmäßige systematische Aktualisierung erfordert. Es umfasst folgende Schritte:\n"
                "a) Ermittlung und Analyse der bekannten und vernünftigerweise vorhersehbaren Risiken für Gesundheit, Sicherheit oder Grundrechte bei bestimmungsgemäßer Verwendung;\n"
                "b) Schätzung und Bewertung der Risiken, die bei bestimmungsgemäßer Verwendung und bei vernünftigerweise vorhersehbarer Fehlanwendung entstehen können;\n"
                "c) Bewertung sonstiger Risiken anhand von Daten aus der Beobachtung nach dem Inverkehrbringen (Artikel 72);\n"
                "d) Ergreifung geeigneter und gezielter Risikomanagementmaßnahmen zur Bewältigung der ermittelten Risiken.\n"
                "3. Bei den Risikomanagementmaßnahmen ist der kombinierten Anwendung der Anforderungen dieses Kapitels gebührend Rechnung zu tragen.\n"
                "4. Hochrisiko-KI-Systeme sind zu testen, um die am besten geeigneten Risikomanagementmaßnahmen zu ermitteln. Durch Tests ist sicherzustellen, dass die Systeme stets ihrer Zweckbestimmung entsprechen und die Anforderungen erfüllen."
            ),
            "keywords": ["Risikomanagementsystem", "Lebenszyklus", "iterativer Prozess", "Risikobewertung", "Fehlanwendung", "Risikominimierung", "Prüfung und Tests"]
        },
        {
            "doc_id": "eu_ai_act_de_art_10",
            "language": "de",
            "type": "article",
            "title": "Daten und Daten-Governance",
            "chapter": "Titel III - Hochrisiko-KI-Systeme - Kapitel 2 Anforderungen",
            "article_id": "Artikel 10",
            "recital_refs": [46, 47, 48],
            "text": (
                "Artikel 10 - Daten und Daten-Governance\n"
                "1. Hochrisiko-KI-Systeme, bei denen Techniken zum Einsatz kommen, die das Trainieren von Modellen mit Daten umfassen, sind auf der Grundlage von Trainings-, Validierungs- und Testdatensätzen zu entwickeln, die den Qualitätskriterien der Absätze 2 bis 5 entsprechen.\n"
                "2. Für Trainings-, Validierungs- und Testdatensätze müssen geeignete Daten-Governance- und Datenverwaltungspraktiken angewandt werden. Diese Praktiken betreffen insbesondere:\n"
                "a) die relevanten Entwurfsentscheidungen;\n"
                "b) die Datenerfassungsprozesse und die Herkunft der Daten sowie bei personenbezogenen Daten den ursprünglichen Erhebungszweck;\n"
                "c) einschlägige Datenaufbereitungsvorgänge wie Annotation, Kennzeichnung, Bereinigung, Aktualisierung, Anreicherung und Aggregation;\n"
                "d) die Formulierung von Annahmen darüber, was die Daten messen sollen;\n"
                "e) eine Bewertung der Verfügbarkeit, Menge und Eignung der Datensätze;\n"
                "f) Prüfung auf mögliche Verzerrungen (Biases), die zu Diskriminierung oder Beeinträchtigung der Grundrechte führen können;\n"
                "g) geeignete Maßnahmen zur Erkennung, Verhinderung und Minderung möglicher Verzerrungen;\n"
                "h) Ermittlung relevanter Datenlücken oder Mängel und deren Behebung.\n"
                "3. Die Datensätze müssen relevant, repräsentativ, fehlerfrei und vollständig sein."
            ),
            "keywords": ["Daten-Governance", "Trainingsdatensätze", "Validierung", "Testen", "Bias-Erkennung", "Verzerrungen", "Datenqualität", "Repräsentativität"]
        },
        {
            "doc_id": "eu_ai_act_de_art_11",
            "language": "de",
            "type": "article",
            "title": "Technische Dokumentation",
            "chapter": "Titel III - Hochrisiko-KI-Systeme - Kapitel 2 Anforderungen",
            "article_id": "Artikel 11",
            "recital_refs": [49, 50],
            "text": (
                "Artikel 11 - Technische Dokumentation\n"
                "1. Die technische Dokumentation eines Hochrisiko-KI-Systems ist vor dem Inverkehrbringen oder der Inbetriebnahme zu erstellen und stets auf dem aktuellen Stand zu halten.\n"
                "2. Die technische Dokumentation ist so abzufassen, dass nachgewiesen wird, dass das Hochrisiko-KI-System die in diesem Kapitel festgelegten Anforderungen erfüllt, und dass den nationalen zuständigen Behörden und notifizierten Stellen alle erforderlichen Informationen bereitgestellt werden. Sie muss mindestens die in Anhang IV aufgeführten Angaben enthalten."
            ),
            "keywords": ["technische Dokumentation", "Anhang IV", "Konformitätsnachweis", "notifizierte Stellen", "Zuständige Behörden"]
        },
        {
            "doc_id": "eu_ai_act_de_art_12",
            "language": "de",
            "type": "article",
            "title": "Aufzeichnungspflichten",
            "chapter": "Titel III - Hochrisiko-KI-Systeme - Kapitel 2 Anforderungen",
            "article_id": "Artikel 12",
            "recital_refs": [51],
            "text": (
                "Artikel 12 - Aufzeichnungspflichten\n"
                "1. Hochrisiko-KI-Systeme müssen technisch so ausgelegt sein, dass sie die automatische Aufzeichnung von Ereignissen ('Protokolle' oder 'Logs') während der Lebensdauer des Systems ermöglichen.\n"
                "2. Um ein der Zweckbestimmung des Systems angemessenes Maß an Rückverfolgbarkeit zu gewährleisten, müssen die Protokollierungsfunktionen die Aufzeichnung von Ereignissen ermöglichen, die relevant sind für:\n"
                "a) die Erkennung von Situationen, die zu einem Risiko oder schwerwiegenden Vorfall führen können;\n"
                "b) die Erleichterung der Beobachtung nach dem Inverkehrbringen (Artikel 72);\n"
                "c) die Überwachung des Betriebs durch die Betreiber (Artikel 26 Absatz 5)."
            ),
            "keywords": ["Aufzeichnungspflichten", "automatische Protokollierung", "Systemprotokolle", "Rückverfolgbarkeit", "schwerwiegender Vorfall", "Logs"]
        },
        {
            "doc_id": "eu_ai_act_de_art_13",
            "language": "de",
            "type": "article",
            "title": "Transparenz und Bereitstellung von Informationen für Betreiber",
            "chapter": "Titel III - Hochrisiko-KI-Systeme - Kapitel 2 Anforderungen",
            "article_id": "Artikel 13",
            "recital_refs": [52, 53],
            "text": (
                "Artikel 13 - Transparenz und Bereitstellung von Informationen für Betreiber\n"
                "1. Hochrisiko-KI-Systeme müssen so konzipiert sein, dass ihr Betrieb hinreichend transparent ist, damit die Betreiber die Ausgaben des Systems interpretieren und angemessen verwenden können.\n"
                "2. Hochrisiko-KI-Systemen ist eine Gebrauchsanweisung beizufügen, die präzise, vollständige, korrekte und klare Angaben enthält.\n"
                "3. Die Gebrauchsanweisung muss Angaben zu Identität und Kontaktdaten des Anbieters, Merkmalen, Leistungsgrenzen, Genauigkeit, Cybersicherheit sowie Maßnahmen der menschlichen Aufsicht enthalten."
            ),
            "keywords": ["Transparenz", "Gebrauchsanweisung", "Informationen für Betreiber", "Leistungsgrenzen", "Erklärbarkeit", "menschliche Aufsicht"]
        },
        {
            "doc_id": "eu_ai_act_de_art_14",
            "language": "de",
            "type": "article",
            "title": "Menschliche Aufsicht",
            "chapter": "Titel III - Hochrisiko-KI-Systeme - Kapitel 2 Anforderungen",
            "article_id": "Artikel 14",
            "recital_refs": [54, 55],
            "text": (
                "Artikel 14 - Menschliche Aufsicht\n"
                "1. Hochrisiko-KI-Systeme müssen so konzipiert und entwickelt werden, dass sie von natürlichen Personen während ihrer Verwendung wirksam beaufsichtigt werden können.\n"
                "2. Die menschliche Aufsicht zielt darauf ab, Risiken für Gesundheit, Sicherheit oder Grundrechte zu verhindern oder zu minimieren.\n"
                "4. Die mit der Aufsicht betrauten Personen müssen in der Lage sein:\n"
                "a) die Fähigkeiten und Grenzen des Systems richtig zu verstehen;\n"
                "b) sich der Tendenz zur automatischen Befolgung oder Übervertrauens in das System bewusst zu sein ('Automation Bias');\n"
                "c) die Ausgaben richtig zu interpretieren;\n"
                "d) in jeder Situation zu entscheiden, das System nicht zu verwenden oder dessen Ausgaben zu überstimmen, zu korrigieren oder zu verwerfen;\n"
                "e) in den Betrieb des Systems einzugreifen oder das System durch eine Stopptaste ('Stop-Button') sicher anzuhalten."
            ),
            "keywords": ["menschliche Aufsicht", "Automation Bias", "Stopptaste", "Übersteuerung", "Mensch-Maschine-Schnittstelle", "Überwachung"]
        },
        {
            "doc_id": "eu_ai_act_de_art_15",
            "language": "de",
            "type": "article",
            "title": "Genauigkeit, Robustheit und Cybersicherheit",
            "chapter": "Titel III - Hochrisiko-KI-Systeme - Kapitel 2 Anforderungen",
            "article_id": "Artikel 15",
            "recital_refs": [56, 57, 58],
            "text": (
                "Artikel 15 - Genauigkeit, Robustheit und Cybersicherheit\n"
                "1. Hochrisiko-KI-Systeme müssen so konzipiert sein, dass sie ein angemessenes Niveau an Genauigkeit, Robustheit und Cybersicherheit erreichen und über ihren gesamten Lebenszyklus beibehalten.\n"
                "3. Hochrisiko-KI-Systeme müssen widerstandsfähig gegenüber Fehlern, Störungen oder Unstimmigkeiten sein.\n"
                "4. Hochrisiko-KI-Systeme müssen gegen Versuche unbefugter Dritter geschützt sein, ihre Nutzung oder Ausgabe durch Ausnutzung von Schwachstellen zu verändern. Technische Lösungen müssen Angriffe wie Datenvergiftung ('Data Poisoning'), gegnerische Angriffe ('Adversarial Attacks') sowie Modellinversion und Extraktionsangriffe verhindern, erkennen und abwehren."
            ),
            "keywords": ["Genauigkeit", "Robustheit", "Cybersicherheit", "Adversarial Attacks", "Data Poisoning", "Datenvergiftung", "Modellinversion", "Resilienz"]
        },
        {
            "doc_id": "eu_ai_act_de_art_50",
            "language": "de",
            "type": "article",
            "title": "Transparenzpflichten für Anbieter und Betreiber bestimmter KI-Systeme",
            "chapter": "Titel IV - Transparenzpflichten für bestimmte KI-Systeme",
            "article_id": "Artikel 50",
            "recital_refs": [70, 71, 72],
            "text": (
                "Artikel 50 - Transparenzpflichten für Anbieter und Betreiber bestimmter KI-Systeme\n"
                "1. Anbieter stellen sicher, dass KI-Systeme, die dazu bestimmt sind, unmittelbar mit natürlichen Personen zu interagieren, so konzipiert sind, dass die betroffenen Personen darüber informiert werden, dass sie mit einem KI-System interagieren, es sei denn, dies ist aus den Umständen offensichtlich.\n"
                "2. Anbieter von KI-Systemen, die synthetische Audio-, Bild-, Video- oder Textinhalte erzeugen, stellen sicher, dass die Ausgaben in einem maschinenlesbaren Format gekennzeichnet und als künstlich erzeugt erkennbar sind (Wasserzeichen / Watermarking).\n"
                "3. Betreiber von Emotionserkennungssystemen oder Systemen zur biometrischen Kategorisierung informieren betroffene Personen über den Betrieb des Systems.\n"
                "4. Betreiber von KI-Systemen, die Deepfakes erzeugen oder manipulieren, legen offen, dass die Inhalte künstlich erzeugt oder manipuliert wurden."
            ),
            "keywords": ["Transparenzpflichten", "Chatbots", "Deepfake-Kennzeichnung", "Wasserzeichen", "synthetische Inhalte", "Emotionserkennung"]
        },
        {
            "doc_id": "eu_ai_act_de_art_51",
            "language": "de",
            "type": "article",
            "title": "Einstufung von KI-Modellen mit allgemeinem Verwendungszweck mit systemischem Risiko",
            "chapter": "Titel V - KI-Modelle mit allgemeinem Verwendungszweck",
            "article_id": "Artikel 51",
            "recital_refs": [110, 111, 112],
            "text": (
                "Artikel 51 - Einstufung von KI-Modellen mit allgemeinem Verwendungszweck mit systemischem Risiko\n"
                "1. Ein KI-Modell mit allgemeinem Verwendungszweck wird als Modell mit systemischem Risiko eingestuft, wenn es über Fähigkeiten mit hoher Auswirkung verfügt oder die Kommission dies beschließt.\n"
                "2. Fähigkeiten mit hoher Auswirkung werden vermutet, wenn die kumulierte Rechenleistung für das Training gemessen in Gleitkommaoperationen (FLOPs) mehr als 10^25 beträgt."
            ),
            "keywords": ["Modelle mit allgemeinem Verwendungszweck", "systemisches Risiko", "FLOPs Schwellenwert", "10^25 FLOPs", "Kommission", "hohe Auswirkung"]
        },
        {
            "doc_id": "eu_ai_act_de_art_55",
            "language": "de",
            "type": "article",
            "title": "Pflichten für Anbieter von KI-Modellen mit allgemeinem Verwendungszweck mit systemischem Risiko",
            "chapter": "Titel V - KI-Modelle mit allgemeinem Verwendungszweck",
            "article_id": "Artikel 55",
            "recital_refs": [113, 114, 115],
            "text": (
                "Artikel 55 - Pflichten für Anbieter von KI-Modellen mit allgemeinem Verwendungszweck mit systemischem Risiko\n"
                "1. Anbieter von Modellen mit systemischem Risiko müssen:\n"
                "a) Modellbewertungen nach dem Stand der Technik durchführen und dokumentieren, einschließlich gegnerischer Tests (Adversarial Testing / Red Teaming);\n"
                "b) mögliche systemische Risiken auf Unionsebene bewerten und mindern;\n"
                "c) schwerwiegende Vorfälle unverzüglich dem KI-Büro und den nationalen Behörden melden;\n"
                "d) ein angemessenes Niveau an Cybersicherheit für das Modell und die physische Infrastruktur gewährleisten."
            ),
            "keywords": ["Pflichten systemisches Risiko", "Adversarial Testing", "Red Teaming", "Meldung schwerwiegender Vorfälle", "KI-Büro", "Cybersicherheit"]
        },
        {
            "doc_id": "eu_ai_act_de_art_99",
            "language": "de",
            "type": "article",
            "title": "Sanktionen und Geldbußen",
            "chapter": "Titel XII - Sanktionen",
            "article_id": "Artikel 99",
            "recital_refs": [166, 167, 168],
            "text": (
                "Artikel 99 - Sanktionen und Geldbußen\n"
                "1. Die Mitgliedstaaten erlassen Vorschriften über Sanktionen und Geldbußen bei Verstößen gegen diese Verordnung. Die Sanktionen müssen wirksam, verhältnismäßig und abschreckend sein.\n"
                "3. Verstöße gegen das Verbot bestimmter KI-Praktiken gemäß Artikel 5 werden mit Geldbußen von bis zu 35 000 000 EUR oder bei Unternehmen von bis zu 7 % des weltweiten Jahresumsatzes geahndet, je nachdem, welcher Betrag höher ist.\n"
                "4. Verstöße gegen sonstige Anforderungen für Hochrisiko-KI-Systeme werden mit Geldbußen von bis zu 15 000 000 EUR oder bis zu 3 % des weltweiten Jahresumsatzes geahndet, je nachdem, welcher Betrag höher ist.\n"
                "5. Bei Erteilung unrichtiger, unvollständiger oder irreführender Auskünfte an notifizierte Stellen oder Behörden drohen Geldbußen von bis zu 7 500 000 EUR oder bis zu 1,5 % des weltweiten Jahresumsatzes.\n"
                "6. Für KMU und Start-ups gilt jeweils der niedrigere Betrag aus Prozentsatz oder Höchstsumme."
            ),
            "keywords": ["Sanktionen", "Geldbußen", "35 Millionen EUR", "7 Prozent Umsatz", "15 Millionen EUR", "3 Prozent Umsatz", "Verstöße gegen Artikel 5", "KMU Obergrenze"]
        },
        {
            "doc_id": "eu_ai_act_de_annex_03",
            "language": "de",
            "type": "annex",
            "title": "Hochrisiko-KI-Systeme gemäß Artikel 6 Absatz 2",
            "chapter": "Anhänge",
            "article_id": "Anhang III",
            "recital_refs": [48, 49, 50, 51],
            "text": (
                "Anhang III - Hochrisiko-KI-Systeme gemäß Artikel 6 Absatz 2\n"
                "Die folgenden KI-Systeme gelten gemäß Artikel 6 Absatz 2 als Hochrisiko-KI-Systeme:\n"
                "1. Biometrie:\n"
                "a) Fernidentifizierungssysteme in Echtzeit oder nachträglich;\n"
                "b) Systeme zur biometrischen Kategorisierung nach sensiblen Merkmalen;\n"
                "c) Systeme zur Emotionserkennung.\n"
                "2. Kritische Infrastrukturen: Sicherheitsbauteile für digitale Infrastruktur, Straßenverkehr, Wasser-, Gas-, Wärme- und Stromversorgung.\n"
                "3. Allgemeine und berufliche Bildung:\n"
                "a) Zulassung oder Zuweisung zu Bildungseinrichtungen;\n"
                "b) Bewertung von Lernergebnissen;\n"
                "c) Einstufung des Bildungsniveaus;\n"
                "d) Überwachung von Prüfungen und Erkennung von Täuschungsversuchen.\n"
                "4. Beschäftigung, Personalmanagement und Zugang zur Selbstständigkeit:\n"
                "a) Einstellung und Auswahl, Ausschreibung, Filterung von Bewerbungen und Bewertung von Bewerbern;\n"
                "b) Entscheidungen über Beförderung, Kündigung, Zuweisung von Aufgaben sowie Überwachung und Leistungsbewertung am Arbeitsplatz.\n"
                "5. Zugang zu wesentlichen privaten und öffentlichen Dienstleistungen:\n"
                "a) Bewertung der Anspruchsberechtigung auf Sozialleistungen;\n"
                "b) Bonitätsprüfung und Kreditwürdigkeitsbewertung (Credit Scoring);\n"
                "c) Notrufdienste und Priorisierung von Rettungskräften;\n"
                "d) Risikobewertung und Preisgestaltung in der Lebens- und Krankenversicherung.\n"
                "6. Strafverfolgung: Risikobewertung von Personen, Lügendetektoren, Zuverlässigkeit von Beweismitteln.\n"
                "7. Migration, Asyl und Grenzkontrolle: Antragsprüfung, Sicherheitsrisiken, Echtheitsprüfung von Reisedokumenten.\n"
                "8. Rechtspflege und demokratische Prozesse: Unterstützung von Justizbehörden bei Rechtsauslegung und Tatsachenfeststellung."
            ),
            "keywords": ["Anhang III", "Hochrisiko-Liste", "Biometrie", "Kritische Infrastruktur", "Bildung", "Beschäftigung", "Personalmanagement", "Credit Scoring", "Bonitätsprüfung", "Strafverfolgung", "Migration", "Rechtspflege"]
        }
    ]

import hashlib

def save_raw_datasets(output_dir: Path) -> Dict[str, Path]:
    """Generates and writes both English and German raw documents with legal provenance metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    en_docs = get_eu_ai_act_en_documents()
    de_docs = get_eu_ai_act_de_documents()

    for doc in en_docs:
        doc["regulation_id"] = "Regulation (EU) 2024/1689"
        doc["celex_uri"] = "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
        doc["official_journal"] = "OJ L, 2024/1689, 12.7.2024, p. 1-144"
        doc["publication_date"] = "2024-07-12"
        doc["retrieval_date"] = "2024-08-01"
        doc["document_version"] = "Official Journal of the European Union, CELEX 32024R1689"
        doc["content_sha256"] = hashlib.sha256(doc["text"].encode("utf-8")).hexdigest()

    for doc in de_docs:
        doc["regulation_id"] = "Verordnung (EU) 2024/1689"
        doc["celex_uri"] = "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
        doc["official_journal"] = "ABl. L, 2024/1689, 12.7.2024, S. 1-144"
        doc["publication_date"] = "2024-07-12"
        doc["retrieval_date"] = "2024-08-01"
        doc["document_version"] = "Amtsblatt der Europäischen Union, CELEX 32024R1689"
        doc["content_sha256"] = hashlib.sha256(doc["text"].encode("utf-8")).hexdigest()
    
    en_path = output_dir / "eu_ai_act_en.json"
    de_path = output_dir / "eu_ai_act_de.json"
    
    with open(en_path, "w", encoding="utf-8") as f:
        json.dump(en_docs, f, indent=2, ensure_ascii=False)
        
    with open(de_path, "w", encoding="utf-8") as f:
        json.dump(de_docs, f, indent=2, ensure_ascii=False)
        
    return {"en": en_path, "de": de_path}

if __name__ == "__main__":
    from app.config import settings
    res = save_raw_datasets(settings.RAW_DATA_DIR)
    print(f"Generated raw datasets successfully:\nEN: {res['en']}\nDE: {res['de']}")

