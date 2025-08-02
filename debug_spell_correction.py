#!/usr/bin/env python3
"""Debug smart search spell correction"""

import asyncio
from app.services.smart_search_service import SmartSearchService
from app.db.database import get_db
from app.utils.spell_checker import check_spelling

def debug_smart_search_spell_correction():
    print("="*80)
    print("DEBUGGING SMART SEARCH SPELL CORRECTION")
    print("="*80)
    
    # Test spell checker directly
    print("\n1. Testing spell checker directly:")
    print("-" * 40)
    result, corrected = check_spelling('shirts')
    print(f"check_spelling('shirts') -> '{result}', corrected: {corrected}")
    
    result2, corrected2 = check_spelling('samung')
    print(f"check_spelling('samung') -> '{result2}', corrected: {corrected2}")
    
    # Test smart search service
    print("\n2. Testing smart search service:")
    print("-" * 40)
    
    async def test_smart_search():
        service = SmartSearchService()
        db = next(get_db())
        
        # Test shirts
        print("Testing 'shirts' with smart search...")
        result = await service.search_products(db, 'shirts', limit=3)
        print(f"  Total Count: {result.total_count}")
        print(f"  Has Typo Correction: {result.has_typo_correction}")
        print(f"  Corrected Query: {result.corrected_query}")
        print(f"  Original Query: {result.query}")
        
        # Test samung
        print("\nTesting 'samung' with smart search...")
        result2 = await service.search_products(db, 'samung', limit=3)
        print(f"  Total Count: {result2.total_count}")
        print(f"  Has Typo Correction: {result2.has_typo_correction}")
        print(f"  Corrected Query: {result2.corrected_query}")
        print(f"  Original Query: {result2.query}")
    
    asyncio.run(test_smart_search())

if __name__ == "__main__":
    debug_smart_search_spell_correction()
