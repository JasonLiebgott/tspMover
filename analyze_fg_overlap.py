#!/usr/bin/env python3

from tsp_allocation_engine import TSPAllocationEngine

def analyze_fg_overlap():
    """Analyze F Fund and G Fund overlap in current allocations"""
    engine = TSPAllocationEngine()
    engine.calculate_recession_score()
    allocation = engine.determine_allocation()
    
    print("=== CURRENT F+G FUND OVERLAP ANALYSIS ===")
    print(f"Recession Score: {engine.recession_score:.1f}/100")
    print()
    print("Current Allocation:")
    for fund, percent in engine.recommended_allocation.items():
        print(f"  {fund} Fund: {percent}%")
    
    f_percent = engine.recommended_allocation['F']
    g_percent = engine.recommended_allocation['G'] 
    total_fixed = f_percent + g_percent
    
    print(f"\nFixed Income Analysis:")
    print(f"  F Fund (Bonds): {f_percent}%")
    print(f"  G Fund (Gov Securities): {g_percent}%") 
    print(f"  Total Fixed Income: {total_fixed}%")
    
    # Show base allocation table for comparison
    base_allocations = engine.get_base_allocations()
    print(f"\n=== BASE ALLOCATION OVERLAPS ===")
    
    for strategy, alloc in base_allocations.items():
        f_base = alloc['F']
        g_base = alloc['G']
        total_base = f_base + g_base
        print(f"{strategy:15s}: F={f_base:2d}% G={g_base:2d}% Total={total_base:2d}%")

if __name__ == "__main__":
    analyze_fg_overlap()