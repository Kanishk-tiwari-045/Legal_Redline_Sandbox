#!/usr/bin/env python3

from utils.risk_detector import RiskDetector

# Test the risk detection with sample problematic clauses
def test_risk_detection():
    detector = RiskDetector()
    
    # Sample problematic clauses that should trigger risk detection
    test_clauses = [
        {
            'clause_id': 'test_1',
            'title': 'Auto-Renewal Clause',
            'text': 'This agreement shall automatically renew for successive one-year periods unless either party provides written notice of termination at least 30 days prior to the expiration date.',
            'page': 1
        },
        {
            'clause_id': 'test_2', 
            'title': 'Termination Clause',
            'text': 'The Company may terminate this agreement immediately at any time for any reason or without cause by providing written notice to the Customer.',
            'page': 2
        },
        {
            'clause_id': 'test_3',
            'title': 'Modification Rights',
            'text': 'Company may modify the terms of this agreement at any time without notice to the customer. Such modifications shall be effective immediately upon posting.',
            'page': 3
        },
        {
            'clause_id': 'test_4',
            'title': 'Late Payment Fee',
            'text': 'Customer agrees to pay a late payment fee of 15% per month on any overdue amounts.',
            'page': 4
        },
        {
            'clause_id': 'test_5',
            'title': 'Liability Limitation',
            'text': 'In no event shall the Company be liable for any consequential, incidental, or punitive damages arising out of this agreement.',
            'page': 5
        }
    ]
    
    document_data = {
        'clauses': test_clauses,
        'total_pages': 5
    }
    
    print("Testing risk detection with sample clauses...")
    risky_clauses = detector.analyze_document(document_data)
    
    print(f"\nResults: Found {len(risky_clauses)} risky clauses out of {len(test_clauses)} total clauses")
    
    for clause in risky_clauses:
        print(f"\nClause: {clause['title']}")
        print(f"Risk Score: {clause['risk_analysis']['score']}")
        print(f"Risk Tags: {clause['risk_analysis']['tags']}")
        print(f"Rationale: {clause['risk_analysis']['rationale']}")
        print("-" * 50)

if __name__ == "__main__":
    test_risk_detection()