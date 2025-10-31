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


def test_simple_bridge_table():
    """Test creating a bridge table."""
    print("Testing bridge table creation...")
    print()

    # Example data
    list_r = ["US", "UK", "DE", "FR"]
    list_s = ["USA", "United Kingdom", "Germany", "France"]

    # Create bridge table
    print("Creating bridge table...")
    bridge_response = requests.post(
        "http://localhost:8000/bridge-table",
        headers={"Content-Type": "application/json"},
        json={"list_r": list_r, "list_s": list_s},
    )

    print(f"Status: {bridge_response.status_code}")
    bridge_data = bridge_response.json()
    print(f"Bridge table created with {bridge_data['total_candidates']} matches")
    print("\nBridge table entries:")
    for entry in bridge_data["bridge_table"]:
        print(f"  '{entry['r_val']}' → '{entry['s_val']}' (PMI: {entry['pmi']:.3f})")
    print()


def test_full_table_join():
    """
    Demonstrate joining two full tables using the three-way semantic join.

    Scenario: Join sales data (with country names) to tax rates (with country codes).
    These tables CANNOT be joined with traditional equi-join because:
    - Sales table has: "germany", "austria", "united kingdom"
    - Tax table has: "de", "gm", "at", "au", "uk"

    Semantic join solves this by finding the semantic relationship.
    """
    print("=" * 60)
    print("THREE-WAY SEMANTIC JOIN DEMONSTRATION")
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
        json={"list_r": list_r, "list_s": list_s},
    )
    bridge_data = bridge_response.json()

    print(f"Found {bridge_data['total_candidates']} best matches:")
    for entry in bridge_data["bridge_table"]:
        print(f"  '{entry['r_val']}' → '{entry['s_val']}' (PMI: {entry['pmi']:.3f})")
    print()

    # Step 2: Perform three-way join
    print("Step 2: Performing three-way join (sales ⋈ bridge ⋈ tax)...")
    join_response = requests.post(
        "http://localhost:8000/join-from-bridge",
        headers={"Content-Type": "application/json"},
        json={
            "list_r": sales_table,
            "r_join_col": "country",
            "bridge_table": bridge_data["bridge_table"],
            "list_s": tax_table,
            "s_join_col": "code",
        },
    )

    join_data = join_response.json()
    print(f"Status: {join_response.status_code}")
    print(
        f"Matched {join_data['matched_count']} out of {join_data['total_r_records']} records"
    )
    print()

    print("FINAL JOINED TABLE:")
    print(json.dumps(join_data["result"], indent=2))
    print()

    print("✅ Successfully joined tables using three-way semantic join!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Semantic Join API - Client Examples")
        print("=" * 60)
        print()

        test_health_check()
        test_simple_bridge_table()
        test_full_table_join()

        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the API server.")
        print("Please make sure the server is running:")
        print("  uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"ERROR: {e}")
