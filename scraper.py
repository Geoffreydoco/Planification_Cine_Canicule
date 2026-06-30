import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime, timedelta

CINEMA_IDS = {
    "Pathé Bellecour":   "P0012",
    "Lumière Terreaux":  "P0017",
    "Lumière Fourmi":    "W6903",
    "Lumière Bellecour": "P0015",
    "Le Cinéma":         "P0009",
    "Cinéma Opéra":      "P0006",
    "Le Zola":           "P0014",
    "UGC Part-Dieu":     "P0036",
    "Institut Lumière":  "P0050",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
