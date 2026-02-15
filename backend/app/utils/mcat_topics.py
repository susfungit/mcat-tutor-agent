"""MCAT taxonomy: 4 sections, topics, and subtopics with helper functions."""

from typing import Dict, List, Optional

MCAT_TAXONOMY: Dict[str, Dict[str, List[str]]] = {
    "Chemical and Physical Foundations of Biological Systems": {
        "General Chemistry": [
            "Atomic Structure",
            "Periodic Table Trends",
            "Bonding and Chemical Interactions",
            "Stoichiometry",
            "Thermodynamics and Thermochemistry",
            "Kinetics",
            "Equilibrium",
            "Acids and Bases",
            "Solubility",
            "Electrochemistry",
        ],
        "Organic Chemistry": [
            "Nomenclature",
            "Stereochemistry",
            "Nucleophilic Substitution and Elimination",
            "Electrophilic Addition",
            "Carbonyl Chemistry",
            "Carboxylic Acid Derivatives",
            "Aromatic Compounds",
            "Separations and Purifications",
            "Spectroscopy",
        ],
        "Physics": [
            "Kinematics and Dynamics",
            "Work, Energy, and Power",
            "Fluids and Solids",
            "Electrostatics and Circuits",
            "Magnetism",
            "Waves and Sound",
            "Light and Optics",
            "Atomic and Nuclear Phenomena",
        ],
        "Biochemistry": [
            "Amino Acids and Proteins",
            "Enzyme Kinetics",
            "Carbohydrate Metabolism",
            "Lipid Metabolism",
        ],
    },
    "Biological and Biochemical Foundations of Living Systems": {
        "Biochemistry": [
            "Amino Acids and Proteins",
            "Enzyme Kinetics",
            "Carbohydrate Structure and Function",
            "Lipid Structure and Function",
            "Nucleotide and Nucleic Acid Structure",
            "Bioenergetics and Metabolism",
            "Glycolysis and Gluconeogenesis",
            "Citric Acid Cycle",
            "Oxidative Phosphorylation",
            "Fatty Acid Metabolism",
            "Amino Acid Metabolism",
        ],
        "Molecular Biology": [
            "DNA Replication",
            "Transcription",
            "Translation",
            "Gene Regulation",
            "Recombinant DNA and Biotechnology",
            "Mutations and Repair",
        ],
        "Cell Biology": [
            "Cell Theory and Structure",
            "Cell Membrane and Transport",
            "Cell Cycle and Mitosis",
            "Meiosis and Genetic Diversity",
            "Cellular Signaling",
            "Apoptosis",
        ],
        "Microbiology": [
            "Bacteria Structure and Growth",
            "Viruses",
            "Fungi and Parasites",
            "Genetics of Prokaryotes",
        ],
        "Organ Systems": [
            "Nervous System",
            "Endocrine System",
            "Cardiovascular System",
            "Respiratory System",
            "Immune System",
            "Digestive System",
            "Renal and Urinary System",
            "Musculoskeletal System",
            "Reproductive System",
            "Integumentary System",
        ],
        "Genetics and Evolution": [
            "Mendelian Genetics",
            "Non-Mendelian Inheritance",
            "Population Genetics",
            "Hardy-Weinberg Equilibrium",
            "Natural Selection and Evolution",
            "Speciation",
        ],
    },
    "Psychological, Social, and Biological Foundations of Behavior": {
        "Psychology": [
            "Sensation and Perception",
            "Learning and Memory",
            "Cognition and Language",
            "Motivation and Emotion",
            "Stress and Coping",
            "Personality",
            "Psychological Disorders",
            "Biological Bases of Behavior",
            "Consciousness and Sleep",
            "Development (Lifespan)",
        ],
        "Sociology": [
            "Social Structure and Stratification",
            "Culture and Socialization",
            "Social Interaction and Groups",
            "Deviance and Social Control",
            "Demographics and Population",
            "Health Disparities",
        ],
        "Biology of Behavior": [
            "Nervous System and Behavior",
            "Neurotransmitters and Drugs",
            "Endocrine System and Behavior",
            "Genetics and Behavior",
        ],
    },
    "Critical Analysis and Reasoning Skills": {
        "Reading Comprehension": [
            "Main Idea and Argument",
            "Inference and Assumption",
            "Tone and Rhetoric",
            "Evidence Evaluation",
        ],
        "Reasoning Skills": [
            "Logical Reasoning",
            "Analogy and Metaphor",
            "Application of Ideas",
            "Integration of Information",
        ],
        "Passage Analysis": [
            "Humanities Passages",
            "Social Sciences Passages",
            "Ethics and Philosophy",
        ],
    },
}


def list_sections() -> List[str]:
    """Return all MCAT section names."""
    return list(MCAT_TAXONOMY.keys())


def list_topics(section: str) -> List[str]:
    """Return all topics for a given section. Raises KeyError if section not found."""
    if section not in MCAT_TAXONOMY:
        raise KeyError(f"Unknown section: {section}")
    return list(MCAT_TAXONOMY[section].keys())


def list_subtopics(section: str, topic: str) -> List[str]:
    """Return all subtopics for a given section and topic."""
    if section not in MCAT_TAXONOMY:
        raise KeyError(f"Unknown section: {section}")
    if topic not in MCAT_TAXONOMY[section]:
        raise KeyError(f"Unknown topic '{topic}' in section '{section}'")
    return MCAT_TAXONOMY[section][topic]


def search_topics(query: str) -> List[Dict[str, str]]:
    """Search for topics/subtopics matching a query string (case-insensitive).

    Returns list of dicts with keys: section, topic, subtopic (if matched at subtopic level).
    """
    query_lower = query.lower()
    results = []
    for section, topics in MCAT_TAXONOMY.items():
        for topic, subtopics in topics.items():
            if query_lower in topic.lower():
                results.append({"section": section, "topic": topic})
            for subtopic in subtopics:
                if query_lower in subtopic.lower():
                    results.append(
                        {"section": section, "topic": topic, "subtopic": subtopic}
                    )
    return results


def validate_topic(section: str, topic: str) -> bool:
    """Check if a section/topic combination exists in the taxonomy."""
    return section in MCAT_TAXONOMY and topic in MCAT_TAXONOMY[section]
