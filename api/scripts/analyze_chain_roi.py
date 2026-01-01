"""Analyze ROI for each chain to prioritize work."""

# Chain data
chains = [
    {"name": "Liquor Centre", "expected": 240, "current": 0, "difficulty": "medium"},
    {"name": "Liquorland", "expected": 170, "current": 0, "difficulty": "medium"},
    {"name": "New World", "expected": 150, "current": 0, "difficulty": "low"},
    {"name": "Bottle O", "expected": 114, "current": 0, "difficulty": "medium"},
    {"name": "Thirsty Liquor", "expected": 106, "current": 0, "difficulty": "medium"},
    {"name": "PAK'nSAVE", "expected": 61, "current": 0, "difficulty": "low"},
    {"name": "Black Bull", "expected": 59, "current": 0, "difficulty": "high"},
    {"name": "Big Barrel", "expected": 51, "current": 0, "difficulty": "medium"},
    {"name": "Glengarry", "expected": 18, "current": 0, "difficulty": "low"},
]

# Difficulty multipliers (effort required)
difficulty_scores = {
    "low": 1.0,      # Proven method works, likely has API
    "medium": 1.5,   # Standard scraping + geocoding
    "high": 2.5,     # Complex scraping, may need manual work
}

# Calculate ROI score
TARGET_COVERAGE = 0.90  # 90%

print("=" * 80)
print("CHAIN PRIORITIZATION BY ROI")
print("=" * 80)
print()
print("ROI Formula: (Stores to Add × Impact) / Effort")
print("  - Stores to Add: Expected × 90% - Current")
print("  - Impact: Store count weight (larger chains = more impact)")
print("  - Effort: Difficulty multiplier")
print()

results = []
for chain in chains:
    stores_needed = int(chain["expected"] * TARGET_COVERAGE) - chain["current"]
    effort = difficulty_scores[chain["difficulty"]]

    # Impact is the number of stores (more stores = more impact)
    impact = stores_needed

    # ROI = Impact / Effort
    roi_score = impact / effort

    results.append({
        **chain,
        "stores_needed": stores_needed,
        "effort": effort,
        "roi_score": roi_score
    })

# Sort by ROI score (descending)
results.sort(key=lambda x: x["roi_score"], reverse=True)

print(f"{'Rank':<5} {'Chain':<20} {'Stores':<8} {'Difficulty':<12} {'ROI Score':<10}")
print("-" * 80)

for i, result in enumerate(results, 1):
    print(f"{i:<5} {result['name']:<20} {result['stores_needed']:<8} "
          f"{result['difficulty']:<12} {result['roi_score']:<10.1f}")

print()
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()

# Top 3 recommendations
print("🥇 TOP PRIORITY:")
top = results[0]
print(f"   {top['name']} - {top['stores_needed']} stores")
print(f"   ROI Score: {top['roi_score']:.1f}")
print(f"   Reasoning: ", end="")
if top['name'] == "Liquor Centre":
    print("Largest chain, biggest coverage impact")
elif top['name'] == "New World":
    print("Part of Foodstuffs, likely has API like PAK'nSAVE")
elif top['name'] == "Liquorland":
    print("Large chain with good store count")
print()

print("🥈 SECOND CHOICE:")
second = results[1]
print(f"   {second['name']} - {second['stores_needed']} stores")
print(f"   ROI Score: {second['roi_score']:.1f}")
print()

print("🥉 THIRD CHOICE:")
third = results[2]
print(f"   {third['name']} - {third['stores_needed']} stores")
print(f"   ROI Score: {third['roi_score']:.1f}")
print()

print("=" * 80)
print("STRATEGIC GROUPINGS")
print("=" * 80)
print()

print("📦 FOODSTUFFS GROUP (Shared Infrastructure):")
foodstuffs = [r for r in results if r['name'] in ['New World', "PAK'nSAVE"]]
total_stores = sum(r['stores_needed'] for r in foodstuffs)
print(f"   New World + PAK'nSAVE = {total_stores} stores combined")
print(f"   Combined ROI if tackled together: Very High")
print(f"   Same API/methods likely work for both")
print()

print("🎯 QUICK WINS (Small chains, low effort):")
quick_wins = [r for r in results if r['expected'] < 100 and r['difficulty'] == 'low']
if quick_wins:
    for qw in quick_wins:
        print(f"   - {qw['name']}: {qw['stores_needed']} stores (difficulty: {qw['difficulty']})")
else:
    print("   - Glengarry: 17 stores (small but easy)")
print()

print("💪 BIG IMPACT (Most stores added):")
big_impact = sorted(results, key=lambda x: x['stores_needed'], reverse=True)[:3]
for bi in big_impact:
    print(f"   {bi['stores_needed']} stores - {bi['name']}")
