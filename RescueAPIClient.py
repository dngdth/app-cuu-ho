#!/usr/bin/env python3
"""
Test script for Rescue API Clients
This script demonstrates how to use the modular API clients to interact with the Rescue API.
"""

import sys
import os
import time
from typing import Dict, Any

# Add the current directory to Python path to import clients
sys.path.insert(0, os.path.dirname(__file__))

from clients import RescueAPIClient
from clients.rescue_request_client import RescueRequestClient
from clients.needs_client import NeedsClient
from clients.disaster_type_client import DisasterTypeClient
from clients.region_client import RegionClient
from clients.geocode_client import GeocodeClient
from clients.health_client import HealthClient


def test_health_check(client: RescueAPIClient) -> bool:
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        health = client.health.check()
        print(f"✅ API Health: {health}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_geocoding(client: RescueAPIClient) -> bool:
    """Test geocoding functionality"""
    print("\n📍 Testing geocoding...")
    try:
        # Test forward geocoding
        address = "Quận 2, Hồ Chí Minh"
        coords = client.geocode.forward_geocode(address)
        print(f"✅ Geocoded '{address}': {coords}")
        return True
    except Exception as e:
        print(f"❌ Geocoding failed: {e}")
        return False


def test_needs_operations(client: RescueAPIClient) -> bool:
    """Test needs CRUD operations"""
    print("\n🛟 Testing needs operations...")
    try:
        # Get all needs
        needs = client.needs.get_all()
        print(f"✅ Found {len(needs)} needs")

        # Create a test need
        test_need = {
            "name": "Test Food Supplies",
            "description": "Emergency food supplies for testing"
        }
        created_need = client.needs.create(test_need)
        need_id = created_need.get('id')
        print(f"✅ Created need with ID: {need_id}")

        # Get the created need
        retrieved_need = client.needs.get_by_id(need_id)
        print(f"✅ Retrieved need: {retrieved_need.get('name')}")

        # Update the need
        update_data = {
            "name": "Updated Test Food Supplies",
            "description": "Updated emergency food supplies"
        }
        updated_need = client.needs.update(need_id, update_data)
        print(f"✅ Updated need: {updated_need.get('name')}")

        # Delete the test need
        delete_result = client.needs.delete(need_id)
        print(f"✅ Deleted need: {delete_result}")

        return True
    except Exception as e:
        print(f"❌ Needs operations failed: {e}")
        return False


def test_regions(client: RescueAPIClient) -> bool:
    """Test region operations"""
    print("\n🏙️ Testing region operations...")
    try:
        # Get all regions
        regions = client.regions.get_all()
        print(f"✅ Found {len(regions)} regions")

        if regions:
            # Test getting a specific region
            region_id = regions[0].get('id')
            region = client.regions.get_by_id(region_id)
            print(f"✅ Retrieved region: {region.get('name', 'Unknown')}")

        return True
    except Exception as e:
        print(f"❌ Region operations failed: {e}")
        return False


def test_disaster_types(client: RescueAPIClient) -> bool:
    """Test disaster type operations"""
    print("\n🌪️ Testing disaster type operations...")
    try:
        # Get all disaster types
        disaster_types = client.disaster_types.get_all()
        print(f"✅ Found {len(disaster_types)} disaster types")

        if disaster_types:
            # Test getting a specific disaster type
            dt_id = disaster_types[0].get('id')
            dt = client.disaster_types.get_by_id(dt_id)
            print(f"✅ Retrieved disaster type: {dt.get('name', 'Unknown')}")

        return True
    except Exception as e:
        print(f"❌ Disaster type operations failed: {e}")
        return False


def test_rescue_requests(client: RescueAPIClient) -> bool:
    """Test rescue request operations"""
    print("\n📋 Testing rescue request operations...")
    try:
        # Get all rescue requests with pagination
        requests = client.rescue_requests.get_all(limit=5, sort_by="created_date", order="desc")
        print(f"✅ Found {len(requests)} recent rescue requests")

        if requests:
            # Test getting a specific request
            request_id = requests[0].get('id')
            request_detail = client.rescue_requests.get_by_id(request_id)
            print(f"✅ Retrieved request: {request_detail.get('title', 'No title')[:50]}...")

        # Test creating a rescue request (optional - comment out if you don't want to create test data)
        # test_request = {
        #     "content": "Test rescue request - please ignore",
        #     "location": "Test Location"
        # }
        # created_request = client.rescue_requests.create(test_request)
        # print(f"✅ Created test request with ID: {created_request.get('id')}")

        return True
    except Exception as e:
        print(f"❌ Rescue request operations failed: {e}")
        return False


def run_all_tests():
    """Run all API tests"""
    print("🚀 Starting Rescue API Client Tests")
    print("=" * 50)

    # Initialize client
    client = RescueAPIClient()

    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Geocoding", test_geocoding),
        ("Needs CRUD", test_needs_operations),
        ("Regions", test_regions),
        ("Disaster Types", test_disaster_types),
        ("Rescue Requests", test_rescue_requests),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func(client):
            passed += 1
        time.sleep(0.5)  # Small delay between tests

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Make sure the API server is running.")
        return False


def demo_usage():
    """Demonstrate basic usage of individual clients"""
    print("\n📚 Usage Examples:")
    print("-" * 30)

    # Example 1: Using individual clients
    print("1. Using individual clients:")
    print("""
from clients.needs_client import NeedsClient
from clients.geocode_client import GeocodeClient

needs_client = NeedsClient()
geocode_client = GeocodeClient()

# Get all needs
needs = needs_client.get_all()

# Geocode an address
coords = geocode_client.forward_geocode("Quận 1, Hồ Chí Minh")
""")

    # Example 2: Using main client
    print("2. Using main client:")
    print("""
from clients import RescueAPIClient

client = RescueAPIClient()

# All operations available through client
needs = client.needs.get_all()
requests = client.rescue_requests.get_all(limit=10)
coords = client.geocode.forward_geocode("Some address")
""")


if __name__ == "__main__":
    try:
        success = run_all_tests()
        demo_usage()

        if not success:
            print("\n💡 To run the API server:")
            print("1. Make sure Docker is running")
            print("2. Start the database: docker-compose up -d postgres")
            print("3. Start the API: python main.py")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)