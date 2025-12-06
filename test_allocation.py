"""Test script to debug allocation calculation."""
from tsp_allocation_engine import TSPAllocationEngine

# Create engine with 12 years to retirement
print("Creating engine with 12 years to retirement...")
engine = TSPAllocationEngine(years_to_retirement=12)

# Calculate metrics
print("\nCalculating metrics...")
engine.calculate_all_metrics()

# Determine allocation
print("\nDetermining allocation...")
allocation_type, risk_level = engine.determine_allocation()

print(f"\n{'='*60}")
print(f"FINAL RESULTS")
print(f"{'='*60}")
print(f"Recession Score: {engine.recession_score:.1f}%")
print(f"Allocation Type: {allocation_type}")
print(f"Risk Level: {risk_level}")
print(f"\nRecommended Allocation:")
for fund, pct in sorted(engine.recommended_allocation.items()):
    if pct > 0:
        print(f"  {fund} Fund: {pct}%")

print(f"\nTotal: {sum(engine.recommended_allocation.values())}%")
print(f"{'='*60}")
