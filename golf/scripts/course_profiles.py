"""
PGA Tour Course Profiles Database
Skill importance weights for each course based on industry research and historical analysis

Skill Categories (1-10 scale, 10 = most important):
- driving_distance: How much advantage long hitters gain
- driving_accuracy: Value of hitting fairways (narrow fairways, thick rough)
- approach: Quality of iron play into greens
- around_green: Short game importance (small/undulating greens, tough pin positions)
- putting: Putting surface difficulty (speed, slopes, bentgrass vs bermuda)

Course Types:
- BOMBER: Rewards distance off the tee
- PRECISION: Rewards accuracy and ball-striking
- BALL_STRIKER: Rewards tee-to-green excellence
- SCRAMBLER: Rewards short game and putting
- COMPLETE: Balanced requirements

Additional Factors:
- altitude: Elevation effect on distance (1=sea level, 3=high altitude like Tahoe)
- wind_exposure: How exposed to wind (1=sheltered, 3=very exposed)
- green_speed: Green difficulty (1=standard, 3=very fast/difficult)
"""

import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CourseProfile:
    """Represents skill requirements for a PGA Tour course"""
    course_name: str
    course_key: int
    event_name: str
    event_id: int

    # Skill importance weights (1-10)
    driving_distance: float
    driving_accuracy: float
    approach: float
    around_green: float
    putting: float

    # Course characteristics
    course_type: str  # BOMBER, PRECISION, BALL_STRIKER, SCRAMBLER, COMPLETE
    yardage: int
    par: int
    altitude: float  # 1-3
    wind_exposure: float  # 1-3
    green_speed: float  # 1-3

    # Grass types
    fairway_grass: str  # bermuda, bentgrass, paspalum, etc.
    green_grass: str  # bermuda, bentgrass, poa_annua, etc.

    notes: str = ""


# ============================================================================
# PGA TOUR COURSE PROFILES DATABASE
# Based on DataGolf Course Fit Tool methodology and industry analysis
# ============================================================================

COURSE_PROFILES: Dict[int, CourseProfile] = {

    # ==================== SIGNATURE EVENTS ====================

    # Augusta National - Masters (Bombers Paradise, but approach/putting critical)
    14: CourseProfile(
        course_name="Augusta National Golf Club",
        course_key=14,
        event_name="Masters Tournament",
        event_id=14,
        driving_distance=9,  # Length advantage huge
        driving_accuracy=5,  # Wide fairways but position matters
        approach=9,  # Must hit specific spots on greens
        around_green=8,  # Shaved areas, tough chips
        putting=9,  # Fastest greens on Tour, severe slopes
        course_type="BOMBER",
        yardage=7545,
        par=72,
        altitude=1,
        wind_exposure=1.5,
        green_speed=3,
        fairway_grass="bermuda",
        green_grass="bentgrass",
        notes="Par 5s reachable for long hitters. Greens extremely fast and undulating."
    ),

    # TPC Sawgrass - THE PLAYERS
    11: CourseProfile(
        course_name="TPC Sawgrass (THE PLAYERS Stadium Course)",
        course_key=11,
        event_name="THE PLAYERS Championship",
        event_id=11,
        driving_distance=6,
        driving_accuracy=8,  # Tight fairways, water everywhere
        approach=9,  # Island green, demanding approaches
        around_green=7,
        putting=8,
        course_type="PRECISION",
        yardage=7215,
        par=72,
        altitude=1,
        wind_exposure=2.5,  # Windy Florida location
        green_speed=2.5,
        fairway_grass="bermuda",
        green_grass="bermuda",
        notes="Iconic island green 17th. High variance course, penalties severe."
    ),

    # Quail Hollow - PGA Championship venue
    241: CourseProfile(
        course_name="Quail Hollow Club",
        course_key=241,
        event_name="PGA Championship",
        event_id=33,
        driving_distance=8,
        driving_accuracy=7,
        approach=8,
        around_green=7,
        putting=7,
        course_type="BALL_STRIKER",
        yardage=7600,
        par=71,
        altitude=1,
        wind_exposure=1.5,
        green_speed=2.5,
        fairway_grass="bermuda",
        green_grass="bermuda/bentgrass",
        notes="Green Mile finish. Long and demanding. Rewards elite ball-strikers."
    ),

    # Oakmont - U.S. Open venue
    608: CourseProfile(
        course_name="Oakmont Country Club",
        course_key=608,
        event_name="U.S. Open",
        event_id=26,
        driving_distance=7,
        driving_accuracy=9,  # Church Pews bunkers
        approach=9,
        around_green=8,
        putting=10,  # Fastest greens in championship golf
        course_type="PRECISION",
        yardage=7255,
        par=70,
        altitude=1,
        wind_exposure=2,
        green_speed=3,
        fairway_grass="bentgrass",
        green_grass="bentgrass",
        notes="Church Pews bunkers. Extremely difficult greens. Ultimate test."
    ),

    # Royal Portrush - The Open
    885: CourseProfile(
        course_name="Royal Portrush Golf Club",
        course_key=885,
        event_name="The Open Championship",
        event_id=100,
        driving_distance=7,
        driving_accuracy=8,
        approach=8,
        around_green=9,  # Links short game critical
        putting=7,
        course_type="SCRAMBLER",
        yardage=7344,
        par=71,
        altitude=1,
        wind_exposure=3,  # Exposed links
        green_speed=2,
        fairway_grass="fescue",
        green_grass="fescue",
        notes="Links golf. Wind dominant factor. Ground game essential."
    ),

    # ==================== BOMBER COURSES ====================

    # Kapalua - The Sentry (Elevation changes, wide fairways)
    656: CourseProfile(
        course_name="Plantation Course at Kapalua",
        course_key=656,
        event_name="The Sentry",
        event_id=16,
        driving_distance=10,  # Huge advantage for long hitters
        driving_accuracy=4,  # Very wide fairways
        approach=7,
        around_green=6,
        putting=7,
        course_type="BOMBER",
        yardage=7596,
        par=73,
        altitude=1.5,  # Some elevation
        wind_exposure=2.5,  # Hawaii trade winds
        green_speed=2,
        fairway_grass="paspalum",
        green_grass="bermuda",
        notes="Winners circle event. Par 73. Big hitters dominate historically."
    ),

    # TPC Scottsdale - WM Phoenix Open
    510: CourseProfile(
        course_name="TPC Scottsdale (Stadium Course)",
        course_key=510,
        event_name="WM Phoenix Open",
        event_id=3,
        driving_distance=8,
        driving_accuracy=6,
        approach=8,
        around_green=6,
        putting=7,
        course_type="BOMBER",
        yardage=7261,
        par=71,
        altitude=1.5,  # Desert altitude helps distance
        wind_exposure=1.5,
        green_speed=2,
        fairway_grass="bermuda",
        green_grass="bermuda",
        notes="Birdie fest. Iconic 16th stadium hole. Low scores win."
    ),

    # TPC Craig Ranch - CJ CUP Byron Nelson
    921: CourseProfile(
        course_name="TPC Craig Ranch",
        course_key=921,
        event_name="THE CJ CUP Byron Nelson",
        event_id=19,
        driving_distance=9,
        driving_accuracy=5,
        approach=7,
        around_green=6,
        putting=7,
        course_type="BOMBER",
        yardage=7468,
        par=72,
        altitude=1,
        wind_exposure=2,
        green_speed=2,
        fairway_grass="bermuda",
        green_grass="bentgrass",
        notes="New venue. Plays long. Distance advantage significant."
    ),

    # ==================== PRECISION COURSES ====================

    # Harbour Town - RBC Heritage (Tight, tree-lined)
    12: CourseProfile(
        course_name="Harbour Town Golf Links",
        course_key=12,
        event_name="RBC Heritage",
        event_id=12,
        driving_distance=4,  # Distance NOT rewarded
        driving_accuracy=10,  # Extremely tight
        approach=8,
        around_green=8,
        putting=7,
        course_type="PRECISION",
        yardage=7121,
        par=71,
        altitude=1,
        wind_exposure=2,
        green_speed=2,
        fairway_grass="bermuda",
        green_grass="bermuda",
        notes="Shortest course on Tour. Tree-lined. Accuracy kings thrive."
    ),

    # Colonial - Charles Schwab Challenge
    21: CourseProfile(
        course_name="Colonial Country Club",
        course_key=21,
        event_name="Charles Schwab Challenge",
        event_id=21,
        driving_distance=5,
        driving_accuracy=9,
        approach=8,
        around_green=7,
        putting=8,
        course_type="PRECISION",
        yardage=7209,
        par=70,
        altitude=1,
        wind_exposure=2,
        green_speed=2.5,
        fairway_grass="bermuda",
        green_grass="bentgrass",
        notes="Hogan's Alley. Small greens. Shot shaping essential."
    ),

    # Torrey Pines South - Farmers Insurance Open
    4: CourseProfile(
        course_name="Torrey Pines Golf Course (South Course)",
        course_key=4,
        event_name="Farmers Insurance Open",
        event_id=4,
        driving_distance=7,
        driving_accuracy=7,
        approach=8,
        around_green=7,
        putting=7,
        course_type="BALL_STRIKER",
        yardage=7765,
        par=72,
        altitude=1,
        wind_exposure=2,  # Coastal wind
        green_speed=2,
        fairway_grass="kikuyu",
        green_grass="poa_annua",
        notes="Poa annua greens. Kikuyu rough brutal. Long and demanding."
    ),

    # Innisbrook Copperhead - Valspar Championship
    665: CourseProfile(
        course_name="Innisbrook Resort (Copperhead Course)",
        course_key=665,
        event_name="Valspar Championship",
        event_id=475,
        driving_distance=5,
        driving_accuracy=9,
        approach=8,
        around_green=8,
        putting=7,
        course_type="PRECISION",
        yardage=7340,
        par=71,
        altitude=1,
        wind_exposure=1.5,
        green_speed=2,
        fairway_grass="bermuda",
        green_grass="bermuda",
        notes="Snake Pit finish. Tree-lined. Demands precision."
    ),

    # ==================== PUTTING COURSES ====================

    # East Lake - Tour Championship
    688: CourseProfile(
        course_name="East Lake Golf Club",
        course_key=688,
        event_name="TOUR Championship",
        event_id=60,
        driving_distance=7,
        driving_accuracy=7,
        approach=8,
        around_green=7,
        putting=9,  # Bentgrass, fast and true
        course_type="BALL_STRIKER",
        yardage=7346,
        par=70,
        altitude=1,
        wind_exposure=1.5,
        green_speed=2.5,
        fairway_grass="bermuda",
        green_grass="bentgrass",
        notes="FedEx Cup finale. Elite field. Putting separates contenders."
    ),

    # TPC Southwind - FedEx St. Jude
    513: CourseProfile(
        course_name="TPC Southwind",
        course_key=513,
        event_name="FedEx St. Jude Championship",
        event_id=27,
        driving_distance=6,
        driving_accuracy=8,
        approach=8,
        around_green=7,
        putting=8,
        course_type="PRECISION",
        yardage=7243,
        par=70,
        altitude=1,
        wind_exposure=1.5,
        green_speed=2.5,
        fairway_grass="bermuda",
        green_grass="bermuda",
        notes="First playoff event. Premium on accuracy and putting."
    ),

    # Muirfield Village - Memorial Tournament
    23: CourseProfile(
        course_name="Muirfield Village Golf Club",
        course_key=23,
        event_name="the Memorial Tournament",
        event_id=23,
        driving_distance=7,
        driving_accuracy=7,
        approach=9,
        around_green=8,
        putting=8,
        course_type="BALL_STRIKER",
        yardage=7543,
        par=72,
        altitude=1,
        wind_exposure=1.5,
        green_speed=2.5,
        fairway_grass="bentgrass",
        green_grass="bentgrass",
        notes="Jack's Place. Rewards complete game. Approach key."
    ),

    # ==================== SCRAMBLER/SHORT GAME COURSES ====================

    # Pebble Beach - AT&T Pebble Beach Pro-Am
    5: CourseProfile(
        course_name="Pebble Beach Golf Links",
        course_key=5,
        event_name="AT&T Pebble Beach Pro-Am",
        event_id=5,
        driving_distance=5,
        driving_accuracy=8,
        approach=8,
        around_green=9,  # Small greens, recovery shots key
        putting=8,  # Poa annua
        course_type="SCRAMBLER",
        yardage=6972,
        par=72,
        altitude=1,
        wind_exposure=2.5,  # Coastal winds
        green_speed=2,
        fairway_grass="poa_annua",
        green_grass="poa_annua",
        notes="Iconic ocean holes. Short game critical. Weather factor."
    ),

    # TPC River Highlands - Travelers Championship
    503: CourseProfile(
        course_name="TPC River Highlands",
        course_key=503,
        event_name="Travelers Championship",
        event_id=34,
        driving_distance=6,
        driving_accuracy=7,
        approach=8,
        around_green=8,
        putting=8,
        course_type="SCRAMBLER",
        yardage=6841,
        par=70,
        altitude=1,
        wind_exposure=1.5,
        green_speed=2,
        fairway_grass="bentgrass",
        green_grass="bentgrass",
        notes="Short course. Low scores. Birdie opportunities but must convert."
    ),

    # Waialae CC - Sony Open
    6: CourseProfile(
        course_name="Waialae Country Club",
        course_key=6,
        event_name="Sony Open in Hawaii",
        event_id=6,
        driving_distance=5,
        driving_accuracy=7,
        approach=7,
        around_green=8,
        putting=8,
        course_type="SCRAMBLER",
        yardage=7044,
        par=70,
        altitude=1,
        wind_exposure=2,  # Trade winds
        green_speed=2,
        fairway_grass="bermuda",
        green_grass="bermuda",
        notes="Short, birdie-fest. Winners often -20 or better."
    ),

    # Sea Island - RSM Classic
    776: CourseProfile(
        course_name="Sea Island Golf Club (Seaside Course)",
        course_key=776,
        event_name="The RSM Classic",
        event_id=493,
        driving_distance=5,
        driving_accuracy=8,
        approach=7,
        around_green=8,
        putting=8,
        course_type="SCRAMBLER",
        yardage=7055,
        par=70,
        altitude=1,
        wind_exposure=2,
        green_speed=2,
        fairway_grass="bermuda",
        green_grass="bermuda",
        notes="Fall Series. Wind can be factor. Short game critical."
    ),

    # ==================== COMPLETE/BALANCED COURSES ====================

    # Bay Hill - Arnold Palmer Invitational
    9: CourseProfile(
        course_name="Arnold Palmer's Bay Hill Club & Lodge",
        course_key=9,
        event_name="Arnold Palmer Invitational",
        event_id=9,
        driving_distance=7,
        driving_accuracy=7,
        approach=8,
        around_green=7,
        putting=8,
        course_type="COMPLETE",
        yardage=7466,
        par=72,
        altitude=1,
        wind_exposure=2,
        green_speed=2,
        fairway_grass="bermuda",
        green_grass="bermuda",
        notes="Tests all aspects. Historically higher winning scores."
    ),

    # TPC Twin Cities - 3M Open
    883: CourseProfile(
        course_name="TPC Twin Cities",
        course_key=883,
        event_name="3M Open",
        event_id=525,
        driving_distance=7,
        driving_accuracy=7,
        approach=7,
        around_green=7,
        putting=7,
        course_type="COMPLETE",
        yardage=7431,
        par=71,
        altitude=1,
        wind_exposure=1.5,
        green_speed=2,
        fairway_grass="bentgrass",
        green_grass="bentgrass",
        notes="Balanced test. Bentgrass throughout."
    ),

    # Sedgefield CC - Wyndham Championship
    752: CourseProfile(
        course_name="Sedgefield Country Club",
        course_key=752,
        event_name="Wyndham Championship",
        event_id=13,
        driving_distance=5,
        driving_accuracy=8,
        approach=8,
        around_green=7,
        putting=8,
        course_type="PRECISION",
        yardage=7127,
        par=70,
        altitude=1,
        wind_exposure=1.5,
        green_speed=2,
        fairway_grass="bermuda",
        green_grass="bermuda",
        notes="Last regular season event. Shorter course rewards accuracy."
    ),

    # ==================== ALTITUDE COURSES ====================

    # Tahoe - Barracuda Championship (Stableford format)
    931: CourseProfile(
        course_name="Tahoe Mountain Club (Old Greenwood)",
        course_key=931,
        event_name="Barracuda Championship",
        event_id=472,
        driving_distance=8,  # Altitude adds 10-15%
        driving_accuracy=7,
        approach=7,
        around_green=7,
        putting=7,
        course_type="BOMBER",
        yardage=7480,
        par=71,
        altitude=3,  # High altitude ~6,000 ft
        wind_exposure=1.5,
        green_speed=2,
        fairway_grass="bentgrass",
        green_grass="bentgrass",
        notes="Modified Stableford scoring. Altitude adds 10-15% to distance."
    ),

    # ==================== INTERNATIONAL COURSES ====================

    # Renaissance Club - Genesis Scottish Open
    977: CourseProfile(
        course_name="The Renaissance Club",
        course_key=977,
        event_name="Genesis Scottish Open",
        event_id=541,
        driving_distance=6,
        driving_accuracy=8,
        approach=8,
        around_green=9,
        putting=7,
        course_type="SCRAMBLER",
        yardage=7293,
        par=70,
        altitude=1,
        wind_exposure=3,  # Links, very exposed
        green_speed=2,
        fairway_grass="fescue",
        green_grass="fescue",
        notes="Links golf prep for The Open. Wind dominant. Ground game essential."
    ),

    # Vidanta Vallarta - Mexico Open
    978: CourseProfile(
        course_name="Vidanta Vallarta",
        course_key=978,
        event_name="Mexico Open",
        event_id=540,
        driving_distance=7,
        driving_accuracy=6,
        approach=7,
        around_green=7,
        putting=7,
        course_type="COMPLETE",
        yardage=7456,
        par=71,
        altitude=1,
        wind_exposure=1.5,
        green_speed=2,
        fairway_grass="paspalum",
        green_grass="paspalum",
        notes="Resort course. More forgiving. Birdie opportunities."
    ),

    # El Cardonal - World Wide Technology Championship
    919: CourseProfile(
        course_name="El Cardonal at Diamante",
        course_key=919,
        event_name="World Wide Technology Championship",
        event_id=457,
        driving_distance=7,
        driving_accuracy=6,
        approach=7,
        around_green=7,
        putting=8,
        course_type="COMPLETE",
        yardage=7452,
        par=72,
        altitude=1,
        wind_exposure=2,  # Coastal
        green_speed=2,
        fairway_grass="paspalum",
        green_grass="paspalum",
        notes="Tiger design. Fall event. Coastal winds can be factor."
    ),
}


class CourseAnalyzer:
    """Analyze course fit for players based on their skill profiles"""

    def __init__(self):
        self.profiles = COURSE_PROFILES

    def get_profile(self, course_key: int) -> Optional[CourseProfile]:
        """Get course profile by course_key"""
        return self.profiles.get(course_key)

    def get_profile_by_event(self, event_id: int) -> Optional[CourseProfile]:
        """Get course profile by event_id"""
        for profile in self.profiles.values():
            if profile.event_id == event_id:
                return profile
        return None

    def get_skill_weights(self, course_key: int) -> Dict[str, float]:
        """Get normalized skill weights for a course"""
        profile = self.get_profile(course_key)
        if not profile:
            return {}

        total = (profile.driving_distance + profile.driving_accuracy +
                 profile.approach + profile.around_green + profile.putting)

        return {
            'driving_distance': profile.driving_distance / total,
            'driving_accuracy': profile.driving_accuracy / total,
            'approach': profile.approach / total,
            'around_green': profile.around_green / total,
            'putting': profile.putting / total,
        }

    def calculate_course_fit(
        self,
        course_key: int,
        player_skills: Dict[str, float]
    ) -> float:
        """
        Calculate course fit score for a player

        Args:
            course_key: Course identifier
            player_skills: Dict with keys 'sg_ott', 'sg_app', 'sg_arg', 'sg_putt', 'driving_distance'

        Returns:
            Course fit score (higher = better fit)
        """
        profile = self.get_profile(course_key)
        if not profile:
            return 0.0

        weights = self.get_skill_weights(course_key)

        # Map player skills to course requirements
        fit_score = 0.0

        # Driving - combine distance and accuracy importance
        if 'sg_ott' in player_skills:
            driving_weight = weights.get('driving_distance', 0) + weights.get('driving_accuracy', 0)
            fit_score += player_skills['sg_ott'] * driving_weight

        # Approach
        if 'sg_app' in player_skills:
            fit_score += player_skills['sg_app'] * weights.get('approach', 0)

        # Around Green
        if 'sg_arg' in player_skills:
            fit_score += player_skills['sg_arg'] * weights.get('around_green', 0)

        # Putting
        if 'sg_putt' in player_skills:
            fit_score += player_skills['sg_putt'] * weights.get('putting', 0)

        return fit_score

    def get_similar_courses(self, course_key: int, top_n: int = 5) -> List[tuple]:
        """Find courses with similar skill requirements"""
        target = self.get_profile(course_key)
        if not target:
            return []

        similarities = []
        for key, profile in self.profiles.items():
            if key == course_key:
                continue

            # Calculate similarity based on skill weights
            diff = (
                abs(target.driving_distance - profile.driving_distance) +
                abs(target.driving_accuracy - profile.driving_accuracy) +
                abs(target.approach - profile.approach) +
                abs(target.around_green - profile.around_green) +
                abs(target.putting - profile.putting)
            )
            similarity = 1 / (1 + diff)  # Higher = more similar
            similarities.append((profile.course_name, similarity, profile.event_name))

        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_n]

    def get_courses_by_type(self, course_type: str) -> List[CourseProfile]:
        """Get all courses of a specific type"""
        return [p for p in self.profiles.values() if p.course_type == course_type]

    def export_to_dataframe(self) -> pd.DataFrame:
        """Export all profiles to a DataFrame"""
        data = []
        for key, profile in self.profiles.items():
            data.append({
                'course_key': key,
                'course_name': profile.course_name,
                'event_name': profile.event_name,
                'event_id': profile.event_id,
                'course_type': profile.course_type,
                'driving_distance': profile.driving_distance,
                'driving_accuracy': profile.driving_accuracy,
                'approach': profile.approach,
                'around_green': profile.around_green,
                'putting': profile.putting,
                'yardage': profile.yardage,
                'par': profile.par,
                'altitude': profile.altitude,
                'wind_exposure': profile.wind_exposure,
                'green_speed': profile.green_speed,
                'fairway_grass': profile.fairway_grass,
                'green_grass': profile.green_grass,
                'notes': profile.notes,
            })
        return pd.DataFrame(data)


def main():
    """Test the course analyzer"""
    analyzer = CourseAnalyzer()

    print("=" * 60)
    print("PGA TOUR COURSE PROFILES DATABASE")
    print("=" * 60)

    # Show all courses by type
    for course_type in ['BOMBER', 'PRECISION', 'BALL_STRIKER', 'SCRAMBLER', 'COMPLETE']:
        courses = analyzer.get_courses_by_type(course_type)
        print(f"\n{course_type} COURSES ({len(courses)}):")
        for c in courses:
            print(f"  - {c.event_name} @ {c.course_name}")

    # Show example course profile
    print("\n" + "=" * 60)
    print("EXAMPLE: Augusta National (Masters)")
    print("=" * 60)

    augusta = analyzer.get_profile(14)
    if augusta:
        print(f"Course Type: {augusta.course_type}")
        print(f"Yardage: {augusta.yardage} | Par: {augusta.par}")
        print(f"\nSkill Importance (1-10):")
        print(f"  Driving Distance: {augusta.driving_distance}")
        print(f"  Driving Accuracy: {augusta.driving_accuracy}")
        print(f"  Approach: {augusta.approach}")
        print(f"  Around Green: {augusta.around_green}")
        print(f"  Putting: {augusta.putting}")
        print(f"\nNotes: {augusta.notes}")

        print("\nSimilar Courses:")
        for name, sim, event in analyzer.get_similar_courses(14):
            print(f"  {event} @ {name} ({sim:.2%})")

    # Export to CSV
    df = analyzer.export_to_dataframe()
    output_path = "/Users/dickgibbons/AI Projects/sports-betting/PGA_Bets/data/processed/course_profiles.csv"
    df.to_csv(output_path, index=False)
    print(f"\nExported {len(df)} course profiles to {output_path}")


if __name__ == "__main__":
    main()
