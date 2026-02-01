#!/usr/bin/env python3
"""
Debug script to check CORS checkout classification
"""
import pandas as pd
import json

def debug_cors_classification():
    """Debug the CORS checkout ticket classification"""
    
    # Load the tickets
    with open('/Users/mac/Desktop/B076_CC_AgenticAI/dataset/tickets.json', 'r') as f:
        tickets = json.load(f)
    
    # Find the CORS checkout ticket
    cors_ticket = None
    for ticket in tickets:
        if 'CORS error on checkout page' == ticket['subject']:
            cors_ticket = ticket
            break
    
    if not cors_ticket:
        print("❌ CORS checkout ticket not found")
        return
        
    print(f"🔍 Found CORS ticket: {cors_ticket['ticket_id']}")
    print(f"Subject: {cors_ticket['subject']}")
    print(f"Body: {cors_ticket['body']}")
    
    # Create the full text
    full_text = f"{cors_ticket['subject']} {cors_ticket['body']}"
    print(f"\n📝 Full text: {full_text}")
    
    # Check the conditions from the ground truth logic
    text = full_text.lower()
    print(f"\n🔍 Checking classification conditions:")
    
    # Check if it contains checkout terms
    checkout_terms = ['checkout', 'payment', 'cart', 'add to cart']
    has_checkout = any(term in text for term in checkout_terms)
    print(f"Contains checkout terms: {has_checkout}")
    if has_checkout:
        for term in checkout_terms:
            if term in text:
                print(f"  ✓ Found: '{term}'")
    
    # Check if it contains CORS
    has_cors = 'cors' in text
    print(f"Contains 'cors': {has_cors}")
    
    # Final condition
    should_be_platform_bug = has_checkout and has_cors
    print(f"\n🎯 Should be classified as platform_bug: {should_be_platform_bug}")
    
    if should_be_platform_bug:
        print("✅ This ticket should definitely be a platform_bug!")
    else:
        print("❌ Classification logic failed")

if __name__ == '__main__':
    debug_cors_classification()