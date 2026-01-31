"""
Top 50 Soccer Leagues and Cups Configuration
For Global Soccer Schedule Dashboard
"""

# API Configuration
FOOTBALL_API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
FOOTBALL_API_BASE_URL = "https://v3.football.api-sports.io"

ODDS_API_KEY = "518c226b561ad7586ec8c5dd1144e3fb"
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"

# Top 50 Leagues organized by tier
TOP_50_LEAGUES = {
    # Tier 1 - Major European Leagues (10)
    "tier_1_major": [
        {"id": 39, "name": "Premier League", "country": "England", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "odds_key": "soccer_epl"},
        {"id": 140, "name": "La Liga", "country": "Spain", "flag": "🇪🇸", "odds_key": "soccer_spain_la_liga"},
        {"id": 78, "name": "Bundesliga", "country": "Germany", "flag": "🇩🇪", "odds_key": "soccer_germany_bundesliga"},
        {"id": 135, "name": "Serie A", "country": "Italy", "flag": "🇮🇹", "odds_key": "soccer_italy_serie_a"},
        {"id": 61, "name": "Ligue 1", "country": "France", "flag": "🇫🇷", "odds_key": "soccer_france_ligue_one"},
        {"id": 88, "name": "Eredivisie", "country": "Netherlands", "flag": "🇳🇱", "odds_key": "soccer_netherlands_eredivisie"},
        {"id": 94, "name": "Primeira Liga", "country": "Portugal", "flag": "🇵🇹", "odds_key": "soccer_portugal_primeira_liga"},
        {"id": 144, "name": "Pro League", "country": "Belgium", "flag": "🇧🇪", "odds_key": "soccer_belgium_first_div"},
        {"id": 179, "name": "Premiership", "country": "Scotland", "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "odds_key": "soccer_spl"},
        {"id": 235, "name": "Premier League", "country": "Russia", "flag": "🇷🇺", "odds_key": "soccer_russia_premier_league"},
    ],

    # Tier 2 - Secondary European Leagues (10)
    "tier_2_europe": [
        {"id": 40, "name": "Championship", "country": "England", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "odds_key": "soccer_efl_champ"},
        {"id": 141, "name": "La Liga 2", "country": "Spain", "flag": "🇪🇸", "odds_key": "soccer_spain_segunda_division"},
        {"id": 79, "name": "2. Bundesliga", "country": "Germany", "flag": "🇩🇪", "odds_key": "soccer_germany_bundesliga2"},
        {"id": 136, "name": "Serie B", "country": "Italy", "flag": "🇮🇹", "odds_key": "soccer_italy_serie_b"},
        {"id": 62, "name": "Ligue 2", "country": "France", "flag": "🇫🇷", "odds_key": "soccer_france_ligue_two"},
        {"id": 203, "name": "Super Lig", "country": "Turkey", "flag": "🇹🇷", "odds_key": "soccer_turkey_super_league"},
        {"id": 197, "name": "Super League", "country": "Greece", "flag": "🇬🇷", "odds_key": "soccer_greece_super_league"},
        {"id": 207, "name": "Super League", "country": "Switzerland", "flag": "🇨🇭", "odds_key": "soccer_switzerland_superleague"},
        {"id": 218, "name": "Bundesliga", "country": "Austria", "flag": "🇦🇹", "odds_key": "soccer_austria_bundesliga"},
        {"id": 119, "name": "Superliga", "country": "Denmark", "flag": "🇩🇰", "odds_key": "soccer_denmark_superliga"},
    ],

    # Tier 3 - Americas (10)
    "tier_3_americas": [
        {"id": 253, "name": "MLS", "country": "USA", "flag": "🇺🇸", "odds_key": "soccer_usa_mls"},
        {"id": 262, "name": "Liga MX", "country": "Mexico", "flag": "🇲🇽", "odds_key": "soccer_mexico_ligamx"},
        {"id": 71, "name": "Serie A", "country": "Brazil", "flag": "🇧🇷", "odds_key": "soccer_brazil_campeonato"},
        {"id": 128, "name": "Primera Division", "country": "Argentina", "flag": "🇦🇷", "odds_key": "soccer_argentina_primera_division"},
        {"id": 239, "name": "Primera A", "country": "Colombia", "flag": "🇨🇴", "odds_key": "soccer_colombia_primera_a"},
        {"id": 265, "name": "Primera Division", "country": "Chile", "flag": "🇨🇱", "odds_key": "soccer_chile_campeonato"},
        {"id": 281, "name": "Primera Division", "country": "Peru", "flag": "🇵🇪", "odds_key": None},
        {"id": 268, "name": "Primera Division", "country": "Uruguay", "flag": "🇺🇾", "odds_key": None},
        {"id": 279, "name": "Primera Division", "country": "Paraguay", "flag": "🇵🇾", "odds_key": None},
        {"id": 242, "name": "Serie A", "country": "Ecuador", "flag": "🇪🇨", "odds_key": None},
    ],

    # Tier 4 - Asia & Oceania (10)
    "tier_4_asia": [
        {"id": 98, "name": "J1 League", "country": "Japan", "flag": "🇯🇵", "odds_key": "soccer_japan_j_league"},
        {"id": 292, "name": "K League 1", "country": "South Korea", "flag": "🇰🇷", "odds_key": "soccer_korea_kleague1"},
        {"id": 169, "name": "Super League", "country": "China", "flag": "🇨🇳", "odds_key": "soccer_china_superleague"},
        {"id": 188, "name": "A-League", "country": "Australia", "flag": "🇦🇺", "odds_key": "soccer_australia_aleague"},
        {"id": 307, "name": "Pro League", "country": "Saudi Arabia", "flag": "🇸🇦", "odds_key": "soccer_saudi_professional_league"},
        {"id": 310, "name": "Pro League", "country": "UAE", "flag": "🇦🇪", "odds_key": None},
        {"id": 323, "name": "Super League", "country": "India", "flag": "🇮🇳", "odds_key": None},
        {"id": 296, "name": "Thai League 1", "country": "Thailand", "flag": "🇹🇭", "odds_key": None},
        {"id": 274, "name": "Liga 1", "country": "Indonesia", "flag": "🇮🇩", "odds_key": None},
        {"id": 340, "name": "V.League 1", "country": "Vietnam", "flag": "🇻🇳", "odds_key": None},
    ],

    # Tier 5 - Cups & Competitions (10)
    "tier_5_cups": [
        {"id": 2, "name": "UEFA Champions League", "country": "Europe", "flag": "🇪🇺", "odds_key": "soccer_uefa_champs_league"},
        {"id": 3, "name": "UEFA Europa League", "country": "Europe", "flag": "🇪🇺", "odds_key": "soccer_uefa_europa_league"},
        {"id": 848, "name": "UEFA Conference League", "country": "Europe", "flag": "🇪🇺", "odds_key": "soccer_uefa_europa_conference_league"},
        {"id": 45, "name": "FA Cup", "country": "England", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "odds_key": "soccer_fa_cup"},
        {"id": 143, "name": "Copa del Rey", "country": "Spain", "flag": "🇪🇸", "odds_key": "soccer_spain_copa_del_rey"},
        {"id": 81, "name": "DFB Pokal", "country": "Germany", "flag": "🇩🇪", "odds_key": "soccer_germany_dfb_pokal"},
        {"id": 137, "name": "Coppa Italia", "country": "Italy", "flag": "🇮🇹", "odds_key": "soccer_italy_coppa_italia"},
        {"id": 66, "name": "Coupe de France", "country": "France", "flag": "🇫🇷", "odds_key": "soccer_france_coupe_de_france"},
        {"id": 13, "name": "Copa Libertadores", "country": "South America", "flag": "🌎", "odds_key": "soccer_conmebol_copa_libertadores"},
        {"id": 11, "name": "Copa Sudamericana", "country": "South America", "flag": "🌎", "odds_key": "soccer_conmebol_copa_sudamericana"},
    ],
}

# Flatten all leagues for easy access
ALL_LEAGUES = []
for tier_name, leagues in TOP_50_LEAGUES.items():
    for league in leagues:
        league["tier"] = tier_name
        ALL_LEAGUES.append(league)

# Create lookup dictionaries
LEAGUE_BY_ID = {league["id"]: league for league in ALL_LEAGUES}
LEAGUE_IDS = [league["id"] for league in ALL_LEAGUES]

# Region mappings for filtering
REGIONS = {
    "Europe": ["tier_1_major", "tier_2_europe"],
    "Americas": ["tier_3_americas"],
    "Asia & Oceania": ["tier_4_asia"],
    "Cups & Competitions": ["tier_5_cups"],
}

# Get leagues by region
def get_leagues_by_region(region):
    """Get all leagues for a given region"""
    if region == "All":
        return ALL_LEAGUES
    tiers = REGIONS.get(region, [])
    return [league for league in ALL_LEAGUES if league["tier"] in tiers]

# Get leagues by tier
def get_leagues_by_tier(tier_name):
    """Get all leagues for a given tier"""
    return TOP_50_LEAGUES.get(tier_name, [])

# Get current season year based on date
def get_season_year(date):
    """
    Determine the season year based on date.
    European seasons run Aug-May, so Jan-Jul uses previous year.
    """
    month = date.month
    year = date.year
    if month >= 1 and month <= 7:
        return year - 1
    return year
