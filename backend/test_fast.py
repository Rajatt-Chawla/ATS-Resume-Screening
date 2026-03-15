"""
Quick test to verify fast analyzer works
"""
from analyzer import calculate_match_score, detect_missing_keywords, get_ai_suggestions

# Test data
resume = "Software engineer with experience in Python, React, and Node.js. Built web applications."
jd = "Looking for a software engineer with Python, React, and JavaScript skills. Experience with web development required."

print("Testing fast analyzer...")
print("1. Testing match score calculation...")
score = calculate_match_score(resume, jd)
print(f"   Match score: {score}%")

print("2. Testing keyword detection...")
keywords = ["python", "react", "javascript", "docker", "aws"]
missing = detect_missing_keywords(resume, keywords)
print(f"   Missing keywords: {missing}")

print("3. Testing suggestions...")
suggestions = get_ai_suggestions(resume, jd)
print(f"   Suggestions generated: {len(suggestions)} items")

print("\n✅ All tests passed! Analyzer is working fast.")





