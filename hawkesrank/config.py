from __future__ import annotations

from datetime import date


REFERENCE_DATE = date(2026, 6, 1)
TOP_POOL_SIZE = 2_000
INSPECTION_SIZE = 300
FINAL_SIZE = 100

# Explicitly named in the released JD as service/consulting environments.
SERVICE_COMPANIES = {
    "tcs",
    "infosys",
    "wipro",
    "accenture",
    "cognizant",
    "capgemini",
    "hcl",
    "tech mahindra",
    "mindtree",
    "mphasis",
    "genpact",
    "genpact ai",
}

TARGET_LOCATION_TERMS = (
    "pune",
    "noida",
    "delhi",
    "gurgaon",
    "ncr",
    "hyderabad",
    "mumbai",
)

NONTECH_TITLE_TERMS = (
    "hr manager",
    "marketing manager",
    "sales executive",
    "accountant",
    "content writer",
    "graphic designer",
    "customer support",
    "operations manager",
    "project manager",
    "business analyst",
    "mechanical engineer",
    "civil engineer",
)

SOFTWARE_TITLE_TERMS = (
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "full stack",
    "full-stack",
    "cloud engineer",
    "devops",
    "java developer",
    ".net developer",
    "mobile developer",
    "qa engineer",
)

DATA_TITLE_TERMS = (
    "data engineer",
    "analytics engineer",
    "data analyst",
    "backend engineer",
)

ML_TITLE_TERMS = (
    "machine learning",
    "ml engineer",
    "ai engineer",
    "ai specialist",
    "data scientist",
    "applied scientist",
    "applied ml",
    "nlp engineer",
    "computer vision engineer",
    "recommendation systems engineer",
    "search engineer",
)

SENIOR_TITLE_TERMS = (
    "senior",
    "staff",
    "lead",
    "principal",
    "founding",
)

BAND_NAMES = {
    0: "low_relevance",
    1: "software_adjacent",
    2: "data_backend_adjacent",
    3: "applied_ml",
    4: "direct_search_ranking",
    5: "senior_relevance_owner",
}

BAND_BASE = {0: 8.0, 1: 28.0, 2: 48.0, 3: 72.0, 4: 102.0, 5: 126.0}
BAND_CEILING = {0: 55.0, 1: 85.0, 2: 115.0, 3: 150.0, 4: 190.0, 5: 225.0}
