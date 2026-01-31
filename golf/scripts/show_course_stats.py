#!/usr/bin/env python3
"""
Course Statistics Explanation
Shows which strokes-gained statistics matter most for the current tournament course
"""

import sys
import os
import pandas as pd

# Add scripts to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)
sys.path.insert(0, parent_dir)

from course_profiles import COURSE_PROFILES, CourseAnalyzer


def get_course_for_tournament(field_path: str = None) -> dict:
    """Determine which course is being played this week"""
    if field_path is None:
        field_path = os.path.join(parent_dir, 'data', 'raw', 'current_field_pga.csv')
    
    if os.path.exists(field_path):
        field = pd.read_csv(field_path)
        if 'course' in field.columns:
            course_name = field['course'].iloc[0]
            # Find matching profile
            for event_id, profile in COURSE_PROFILES.items():
                if course_name.lower() in profile.course_name.lower() or profile.course_name.lower() in course_name.lower():
                    return {
                        'event_id': event_id,
                        'profile': profile,
                        'found': True
                    }
    
    return {'found': False}


def explain_course_stats(course_profile=None):
    """Generate detailed explanation of course-specific statistics"""
    
    if course_profile is None:
        result = get_course_for_tournament()
        if not result['found']:
            print("⚠️  Could not find course profile for current tournament")
            return None
        course = result['profile']
    else:
        course = course_profile
    
    print("="*80)
    print("COURSE-SPECIFIC STATISTICS ANALYSIS")
    print("="*80)
    
    print(f"\n📍 Course: {course.course_name}")
    print(f"🏆 Event: {course.event_name}")
    print(f"📏 Par: {course.par} | Yardage: {course.yardage:,} yards")
    print(f"📝 Course Type: {course.course_type}")
    
    if course.notes:
        print(f"\n{course.notes}\n")
    
    print("="*80)
    print("STROKES-GAINED STATISTICS IMPORTANCE (1-10 scale)")
    print("="*80)
    
    # Sort skills by importance
    skills = [
        ('🏌️  Around the Green (SG: ARG)', course.around_green, 
         'Short game skills - chipping, sand saves, recovery shots'),
        ('⛳ Putting (SG: PUTT)', course.putting, 
         'Putting performance - especially important on fast/undulating greens'),
        ('🎯 Driving Accuracy', course.driving_accuracy, 
         'Fairways hit - critical on tight courses with thick rough'),
        ('⚡ Approach Play (SG: APP)', course.approach, 
         'Iron play into greens - accuracy and distance control'),
        ('🏌️  Driving Distance (SG: OTT)', course.driving_distance, 
         'Distance off the tee - advantage on long, open courses'),
    ]
    
    skills_sorted = sorted(skills, key=lambda x: x[1], reverse=True)
    
    print(f"\n{'Skill':<40} {'Weight':>8} {'Importance':>15} {'Description'}")
    print("-"*95)
    
    for skill, weight, desc in skills_sorted:
        bar = "█" * int(weight)
        importance = ""
        if weight >= 9:
            importance = "CRITICAL"
        elif weight >= 7:
            importance = "VERY HIGH"
        elif weight >= 5:
            importance = "MODERATE"
        else:
            importance = "LOW"
        print(f"{skill:<40} {weight:>6.1f}/10 {importance:>15} {desc}")
    
    print("\n" + "="*80)
    print("WHAT STATISTICS MATTER MOST FOR THIS COURSE")
    print("="*80)
    
    # Find top 3 skills
    top_skills = skills_sorted[:3]
    
    print(f"\n🎯 Top 3 Most Important Statistics:")
    for i, (skill, weight, desc) in enumerate(top_skills, 1):
        print(f"\n   {i}. {skill.split('(')[0].strip()}")
    print(f"      Weight: {weight}/10 - {importance}")
    print(f"      Why: {desc}")
    
    print(f"\n💡 Betting Strategy:")
    print(f"   • Favor players strong in: {top_skills[0][0].split('(')[0].strip()}")
    print(f"   • Secondary factor: {top_skills[1][0].split('(')[0].strip()}")
    print(f"   • Also consider: {top_skills[2][0].split('(')[0].strip()}")
    
    print(f"\n📊 Course Type Breakdown:")
    course_type_explanation = {
        "BOMBER": "Distance off the tee is KEY - long hitters have significant advantage on par 5s and longer holes",
        "PRECISION": "Accuracy is KEY - players who hit fairways consistently will score better (thick rough penalizes misses)",
        "BALL_STRIKER": "Tee-to-green excellence is KEY - ball striking matters most (approach + driving combined)",
        "SCRAMBLER": "Short game and putting KEY - scrambling ability crucial (small greens, tough pin positions)",
        "COMPLETE": "Balanced course - all-around game needed (no single skill dominates)"
    }
    
    print(f"   • {course.course_type}: {course_type_explanation.get(course.course_type, 'General course requirements')}")
    
    print(f"\n🌱 Course Conditions:")
    if course.fairway_grass and course.green_grass:
        print(f"   • Fairway Grass: {course.fairway_grass.title()}")
        print(f"   • Green Grass: {course.green_grass.title()}")
    if course.wind_exposure:
        wind_level = ["Low", "Moderate", "High"][int(course.wind_exposure) - 1] if course.wind_exposure <= 3 else "Moderate"
        print(f"   • Wind Exposure: {wind_level}")
    if course.green_speed:
        speed_level = ["Standard", "Fast", "Very Fast"][int(course.green_speed) - 1] if course.green_speed <= 3 else "Standard"
        print(f"   • Green Speed: {speed_level}")
    
    print("\n" + "="*80)
    print("KEY TAKEAWAY FOR THIS WEEK'S BETTING")
    print("="*80)
    
    print(f"\n🎯 Focus on players who excel in {top_skills[0][0].split('(')[0].strip()} and {top_skills[1][0].split('(')[0].strip()}")
    print(f"   These two skills account for {(top_skills[0][1] + top_skills[1][1]) / 20 * 100:.0f}% of course importance")
    print(f"\n   When evaluating DataGolf predictions, prioritize players with:")
    print(f"   • Strong {top_skills[0][0].split('(')[0].strip()} ratings")
    print(f"   • Strong {top_skills[1][0].split('(')[0].strip()} ratings")
    print(f"   • Good course history at {course.course_name}")
    
    print("="*80)
    
    return course


if __name__ == "__main__":
    explain_course_stats()
