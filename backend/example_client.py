"""
Example client script to test the Semantic Join API.

Make sure the backend server is running before executing this script:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""
import requests
import json


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check endpoint...")
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_two_step_join():
    """Test the two-step join process."""
    print("Testing two-step join process...")
    print()
    
    # Example data
    list_r = ["US", "UK", "DE", "FR"]
    list_s = ["USA", "United Kingdom", "Germany", "France"]
    
    # Step 1: Create bridge table
    print("Step 1: Creating bridge table...")
    bridge_response = requests.post(
        "http://localhost:8000/bridge-table",
        headers={"Content-Type": "application/json"},
        json={
            "list_r": list_r,
            "list_s": list_s
        }
    )
    
    print(f"Status: {bridge_response.status_code}")
    bridge_data = bridge_response.json()
    print(f"Bridge table created with {bridge_data['total_candidates']} candidates")
    print()
    
    # Step 2: Perform join from bridge table
    print("Step 2: Performing join from bridge table...")
    join_response = requests.post(
        "http://localhost:8000/join-from-bridge",
        headers={"Content-Type": "application/json"},
        json={
            "list_r": list_r,
            "bridge_table": bridge_data["bridge_table"]
        }
    )
    
    print(f"Status: {join_response.status_code}")
    print("\nFinal Result:")
    print(json.dumps(join_response.json(), indent=2))
    print()


def test_full_table_join():
    """
    Demonstrate joining two full tables using semantic join.
    
    Scenario: Join sales data (with country names) to tax rates (with country codes).
    These tables CANNOT be joined with traditional equi-join because:
    - Sales table has: "germany", "austria", "united kingdom"
    - Tax table has: "gm", "de", "at", "au", "uk"
    
    Semantic join solves this by finding the semantic relationship.
    """
    print("=" * 60)
    print("FULL TABLE JOIN DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Table 1: Sales data with country NAMES
    sales_table = [
        {"id": 1, "country": "germany", "revenue": 50000, "year": 2024},
        {"id": 2, "country": "austria", "revenue": 30000, "year": 2024},
        {"id": 3, "country": "united kingdom", "revenue": 75000, "year": 2024},
    ]
    
    # Table 2: Tax rates with country CODES
    tax_table = [
        {"code": "de", "tax_rate": 0.19, "region": "EU"},
        {"code": "gm", "tax_rate": 0.19, "region": "EU"},
        {"code": "at", "tax_rate": 0.20, "region": "EU"},
        {"code": "au", "tax_rate": 0.20, "region": "EU"},
        {"code": "uk", "tax_rate": 0.20, "region": "EU"},
    ]
    
    print("TABLE 1 - Sales Data (with country names):")
    print(json.dumps(sales_table, indent=2))
    print()
    
    print("TABLE 2 - Tax Rates (with country codes):")
    print(json.dumps(tax_table, indent=2))
    print()
    
    print("❌ Traditional JOIN would fail:")
    print("   SELECT * FROM sales JOIN tax ON sales.country = tax.code")
    print("   → No matches because 'germany' ≠ 'de', 'austria' ≠ 'at', etc.")
    print()
    
    # Extract join keys
    list_r = [row["country"] for row in sales_table]
    list_s = [row["code"] for row in tax_table]
    
    print("✅ Semantic JOIN solution:")
    print(f"   Join keys from sales: {list_r}")
    print(f"   Join keys from tax:   {list_s}")
    print()
    
    # Step 1: Create bridge table
    print("Step 1: Creating bridge table...")
    bridge_response = requests.post(
        "http://localhost:8000/bridge-table",
        headers={"Content-Type": "application/json"},
        json={"list_r": list_r, "list_s": list_s}
    )
    bridge_data = bridge_response.json()
    
    print(f"Found {bridge_data['total_candidates']} candidate matches:")
    for entry in bridge_data["bridge_table"]:
        print(f"  '{entry['r_val']}' → '{entry['s_val']}' (PMI: {entry['pmi']:.3f})")
    print()
    
    # Step 2: Perform join
    print("Step 2: Selecting best matches...")
    join_response = requests.post(
        "http://localhost:8000/join-from-bridge",
        headers={"Content-Type": "application/json"},
        json={"list_r": list_r, "bridge_table": bridge_data["bridge_table"]}
    )
    join_map = join_response.json()["result"]
    
    print("Best matches:")
    for country, code in join_map.items():
        print(f"  '{country}' → '{code}'")
    print()
    
    # Step 3: Combine the tables
    print("Step 3: Combining tables...")
    joined_result = []
    for sales_row in sales_table:
        country = sales_row["country"]
        matched_code = join_map.get(country)
        
        if matched_code:
            # Find the matching tax row
            tax_row = next((t for t in tax_table if t["code"] == matched_code), None)
            if tax_row:
                joined_result.append({
                    **sales_row,
                    "matched_code": matched_code,
                    "tax_rate": tax_row["tax_rate"],
                    "region": tax_row["region"],
                })
        else:
            # No match found
            joined_result.append({
                **sales_row,
                "matched_code": None,
                "tax_rate": None,
                "region": None,
            })
    
    print("FINAL JOINED TABLE:")
    print(json.dumps(joined_result, indent=2))
    print()
    
    print("✅ Successfully joined tables using semantic matching!")
    print("=" * 60)
    print()


def test_error_handling():
    """Test error handling with invalid input."""
    print("Testing error handling...")
    
    # Empty list_r
    data = {
        "list_r": [],
        "bridge_table": []
    }
    
    response = requests.post(
        "http://localhost:8000/join-from-bridge",
        headers={"Content-Type": "application/json"},
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    print()


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Semantic Join API - Client Examples")
        print("=" * 60)
        print()
        
        test_health_check()
        test_two_step_join()
        test_full_table_join()
        test_error_handling()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the API server.")
        print("Please make sure the server is running:")
        print("  uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"ERROR: {e}")

