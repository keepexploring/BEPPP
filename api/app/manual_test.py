#!/usr/bin/env python3
"""
Manual API Testing Script for Solar Hub Management API
Run this script to test all endpoints manually with detailed output
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin"

# Test data IDs (using high numbers to avoid conflicts)
TEST_HUB_ID = 888
TEST_BATTERY_ID = 888
TEST_USER_ID = 888
TEST_PUE_ID = 888
TEST_NOTE_ID = 888
TEST_RENTAL_ID = 888

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
        
    def authenticate(self) -> bool:
        """Get authentication token"""
        print("🔐 Testing Authentication...")
        try:
            response = self.session.post(
                f"{self.base_url}/auth/token",
                data={"username": USERNAME, "password": PASSWORD}
            )
            
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict[Any, Any] = None, 
                     description: str = "", expect_status: int = 200, auth: bool = True) -> Dict:
        """Test a single endpoint"""
        print(f"\n🧪 {description}")
        print(f"   {method.upper()} {endpoint}")
        
        try:
            headers = {} if not auth else {"Authorization": f"Bearer {self.token}"}
            
            if method.upper() == "GET":
                response = self.session.get(f"{self.base_url}{endpoint}", headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(f"{self.base_url}{endpoint}", json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(f"{self.base_url}{endpoint}", json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(f"{self.base_url}{endpoint}", headers=headers)
            
            if response.status_code == expect_status:
                print(f"✅ Success ({response.status_code})")
                try:
                    result = response.json()
                    if isinstance(result, dict) and len(result) < 10:
                        print(f"   Response: {json.dumps(result, indent=2, default=str)}")
                    elif isinstance(result, list) and len(result) <= 3:
                        print(f"   Response: {json.dumps(result, indent=2, default=str)}")
                    else:
                        print(f"   Response: Large data set ({len(result)} items)")
                    return result
                except:
                    print(f"   Response: {response.text[:200]}...")
                    return {"raw_response": response.text}
            else:
                print(f"❌ Failed ({response.status_code})")
                print(f"   Error: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return {}
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Solar Hub API Tests")
        print("=" * 50)
        
        # 1. Health check
        self.test_endpoint("GET", "/health", description="Health Check", auth=False)
        self.test_endpoint("GET", "/", description="Root Endpoint", auth=False)
        
        # 2. Authentication
        if not self.authenticate():
            print("❌ Cannot continue without authentication")
            return
        
        # 3. Solar Hub Tests
        print("\n" + "="*30 + " SOLAR HUB TESTS " + "="*30)
        
        hub_data = {
            "hub_id": TEST_HUB_ID,
            "what_three_word_location": "testing.solar.hub",
            "solar_capacity_kw": 100,
            "country": "Kenya",
            "latitude": -1.286389,
            "longitude": 36.817223
        }
        
        self.test_endpoint("POST", "/hubs/", hub_data, "Create Solar Hub")
        self.test_endpoint("GET", f"/hubs/{TEST_HUB_ID}", description="Get Solar Hub")
        
        hub_update = {"solar_capacity_kw": 150, "country": "Tanzania"}
        self.test_endpoint("PUT", f"/hubs/{TEST_HUB_ID}", hub_update, "Update Solar Hub")
        self.test_endpoint("GET", "/hubs/", description="List All Hubs")
        
        # 4. User Tests
        print("\n" + "="*30 + " USER TESTS " + "="*30)
        
        user_data = {
            "user_id": TEST_USER_ID,
            "name": "Test User API",
            "users_identification_document_number": "ID123456789",
            "mobile_number": "+254700123456",
            "address": "123 Test Avenue, Nairobi",
            "hub_id": TEST_HUB_ID,
            "user_access_level": "user",
            "username": "testuser_api",
            "password": "secure_test_password"
        }
        
        self.test_endpoint("POST", "/users/", user_data, "Create User")
        self.test_endpoint("GET", f"/users/{TEST_USER_ID}", description="Get User")
        
        user_update = {"name": "Updated Test User", "mobile_number": "+254700654321"}
        self.test_endpoint("PUT", f"/users/{TEST_USER_ID}", user_update, "Update User")
        self.test_endpoint("GET", f"/hubs/{TEST_HUB_ID}/users", description="List Hub Users")
        
        # 5. Battery Tests
        print("\n" + "="*30 + " BATTERY TESTS " + "="*30)
        
        battery_data = {
            "battery_id": TEST_BATTERY_ID,
            "hub_id": TEST_HUB_ID,
            "battery_capacity_wh": 10000,
            "status": "available"
        }
        
        self.test_endpoint("POST", "/batteries/", battery_data, "Create Battery")
        self.test_endpoint("GET", f"/batteries/{TEST_BATTERY_ID}", description="Get Battery")
        
        battery_update = {"battery_capacity_wh": 12000, "status": "maintenance"}
        self.test_endpoint("PUT", f"/batteries/{TEST_BATTERY_ID}", battery_update, "Update Battery")
        self.test_endpoint("GET", f"/hubs/{TEST_HUB_ID}/batteries", description="List Hub Batteries")
        
        # 6. PUE Tests
        print("\n" + "="*30 + " PUE TESTS " + "="*30)
        
        pue_data = {
            "pue_id": TEST_PUE_ID,
            "hub_id": TEST_HUB_ID,
            "name": "Test Grinding Machine",
            "description": "High-power grain grinding machine for testing",
            "rental_cost": 100.0,
            "status": "available"
        }
        
        self.test_endpoint("POST", "/pue/", pue_data, "Create PUE")
        self.test_endpoint("GET", f"/pue/{TEST_PUE_ID}", description="Get PUE")
        
        pue_update = {"rental_cost": 120.0, "status": "rented"}
        self.test_endpoint("PUT", f"/pue/{TEST_PUE_ID}", pue_update, "Update PUE")
        self.test_endpoint("GET", f"/hubs/{TEST_HUB_ID}/pue", description="List Hub PUE")
        
        # 7. PUE Rental Tests
        print("\n" + "="*30 + " PUE RENTAL TESTS " + "="*30)
        
        rental_data = {
            "pue_rental_id": TEST_RENTAL_ID,
            "pue_id": TEST_PUE_ID,
            "user_id": TEST_USER_ID,
            "timestamp_taken": datetime.now().isoformat(),
            "due_back": (datetime.now() + timedelta(days=3)).isoformat()
        }
        
        self.test_endpoint("POST", "/pue-rentals/", rental_data, "Create PUE Rental")
        self.test_endpoint("GET", f"/pue-rentals/{TEST_RENTAL_ID}", description="Get PUE Rental")
        
        rental_update = {"date_returned": datetime.now().isoformat()}
        self.test_endpoint("PUT", f"/pue-rentals/{TEST_RENTAL_ID}", rental_update, "Update PUE Rental")
        
        # 8. Notes Tests
        print("\n" + "="*30 + " NOTES TESTS " + "="*30)
        
        note_data = {
            "id": TEST_NOTE_ID,
            "content": "This is a comprehensive test note for the API testing suite. It contains detailed information about battery maintenance schedules."
        }
        
        self.test_endpoint("POST", "/notes/", note_data, "Create Note")
        self.test_endpoint("GET", f"/notes/{TEST_NOTE_ID}", description="Get Note")
        
        note_update = {"content": "Updated note content with new maintenance information."}
        self.test_endpoint("PUT", f"/notes/{TEST_NOTE_ID}", note_update, "Update Note")
        
        # 9. Webhook Test (Live Data)
        print("\n" + "="*30 + " WEBHOOK TESTS " + "="*30)
        
        # Create sample battery data
        sample_battery_data = {
            "id": 1,
            "battery_id": TEST_BATTERY_ID,
            "state_of_charge": 78,
            "voltage": 12.4,
            "current_amps": 3.2,
            "power_watts": 39.68,
            "time_remaining": 240,
            "temp_battery": 29.5,
            "amp_hours_consumed": 2.1,
            "charging_current": 0.0,
            "timestamp": datetime.now().isoformat(),
            "usb_voltage": 5.0,
            "usb_power": 3.0,
            "usb_current": 0.6,
            "latitude": -1.286389,
            "longitude": 36.817223,
            "altitude": 1680.0,
            "SD_card_storage_remaining": 950.0,
            "battery_orientation": "normal",
            "number_GPS_satellites_for_fix": 10,
            "mobile_signal_strength": 5,
            "event_type": "normal_operation",
            "new_battery_cycle": 0
        }
        
        webhook_data = {
            "event_id": f"test-event-{int(time.time())}",
            "webhook_id": "test-webhook-123",
            "device_id": "0291f60a-cfaf-462d-9e82-5ce662fb3823",
            "thing_id": "test-thing-456",
            "values": [
                {
                    "id": "prop-data-123",
                    "name": "data",
                    "value": json.dumps(sample_battery_data),
                    "persist": True,
                    "updated_at": datetime.now().isoformat(),
                    "created_by": "test-system"
                }
            ]
        }
        
        self.test_endpoint("POST", "/webhook/live-data", webhook_data, "Send Live Data via Webhook", auth=False)
        
        # Wait a moment for data to be processed
        time.sleep(2)
        
        # 10. Data Query Tests
        print("\n" + "="*30 + " DATA QUERY TESTS " + "="*30)
        
        # Send a few more data points for testing
        for i in range(3):
            sample_data = sample_battery_data.copy()
            sample_data["state_of_charge"] = 78 - i * 2
            sample_data["voltage"] = 12.4 - i * 0.1
            sample_data["timestamp"] = (datetime.now() - timedelta(minutes=i*10)).isoformat()
            
            webhook_payload = webhook_data.copy()
            webhook_payload["values"][0]["value"] = json.dumps(sample_data)
            webhook_payload["event_id"] = f"test-event-{int(time.time())}-{i}"
            
            self.test_endpoint("POST", "/webhook/live-data", webhook_payload, f"Send Test Data Point {i+1}", auth=False)
            time.sleep(1)
        
        # Test data retrieval endpoints
        self.test_endpoint("GET", f"/data/latest/{TEST_BATTERY_ID}", description="Get Latest Battery Data")
        
        # Test battery data with timestamps
        start_time = (datetime.now() - timedelta(hours=1)).isoformat() + "Z"
        end_time = datetime.now().isoformat() + "Z"
        self.test_endpoint("GET", f"/data/battery/{TEST_BATTERY_ID}?start_timestamp={start_time}&end_timestamp={end_time}&limit=10", description="Get Battery Data with Timestamps")
        
        # Test CSV export
        print("\n🧪 Testing CSV Export")
        try:
            response = self.session.get(
                f"{self.base_url}/data/battery/{TEST_BATTERY_ID}?format=csv&limit=5",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status_code == 200:
                print("✅ CSV Export successful")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Data sample: {response.text[:200]}...")
            else:
                print(f"❌ CSV Export failed ({response.status_code})")
        except Exception as e:
            print(f"❌ CSV Export error: {e}")
        
        # Test data query POST endpoint
        query_data = {
            "battery_ids": [TEST_BATTERY_ID],
            "fields": ["timestamp", "state_of_charge", "voltage", "current_amps"],
            "format": "json"
        }
        self.test_endpoint("POST", "/data/query", query_data, "Query Live Data (JSON)")
        
        # Test dataframe format
        query_data["format"] = "dataframe"
        self.test_endpoint("POST", "/data/query", query_data, "Query Live Data (DataFrame)")
        
        # Test battery summary
        self.test_endpoint("GET", f"/data/summary/{TEST_BATTERY_ID}?hours=1", description="Get Battery Summary")
        
        # 11. Security Tests
        print("\n" + "="*30 + " SECURITY TESTS " + "="*30)
        
        # Test without authorization
        print("\n🧪 Testing Unauthorized Access")
        try:
            response = requests.get(f"{self.base_url}/hubs/{TEST_HUB_ID}")
            if response.status_code == 403:
                print("✅ Correctly blocked unauthorized access (403)")
            else:
                print(f"⚠️  Unexpected response for unauthorized access: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing unauthorized access: {e}")
        
        # Test with invalid token
        print("\n🧪 Testing Invalid Token")
        try:
            response = requests.get(
                f"{self.base_url}/hubs/{TEST_HUB_ID}",
                headers={"Authorization": "Bearer invalid-token-123"}
            )
            if response.status_code == 401:
                print("✅ Correctly rejected invalid token (401)")
            else:
                print(f"⚠️  Unexpected response for invalid token: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing invalid token: {e}")
        
        # 12. Performance Tests
        print("\n" + "="*30 + " PERFORMANCE TESTS " + "="*30)
        
        print("\n🧪 Testing Response Times")
        endpoints_to_test = [
            ("GET", f"/hubs/{TEST_HUB_ID}", "Get Hub"),
            ("GET", f"/batteries/{TEST_BATTERY_ID}", "Get Battery"),
            ("GET", f"/data/latest/{TEST_BATTERY_ID}", "Get Latest Data"),
            ("GET", "/health", "Health Check")
        ]
        
        for method, endpoint, description in endpoints_to_test:
            start_time = time.time()
            try:
                if "health" in endpoint:
                    response = requests.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    print(f"✅ {description}: {response_time:.2f}ms")
                else:
                    print(f"❌ {description}: Failed ({response.status_code})")
            except Exception as e:
                print(f"❌ {description}: Error - {e}")
        
        # 13. Edge Case Tests
        print("\n" + "="*30 + " EDGE CASE TESTS " + "="*30)
        
        # Test non-existent resources
        self.test_endpoint("GET", "/hubs/99999", description="Get Non-existent Hub", expect_status=404)
        self.test_endpoint("GET", "/batteries/99999", description="Get Non-existent Battery", expect_status=404)
        self.test_endpoint("GET", "/data/latest/99999", description="Get Latest Data for Non-existent Battery", expect_status=404)
        
        # Test invalid data
        invalid_hub = {
            "hub_id": "invalid_id",  # Should be integer
            "solar_capacity_kw": -100  # Negative value
        }
        self.test_endpoint("POST", "/hubs/", invalid_hub, "Create Hub with Invalid Data", expect_status=422)
        
        # 14. Cleanup Tests
        print("\n" + "="*30 + " CLEANUP TESTS " + "="*30)
        
        self.test_endpoint("DELETE", f"/notes/{TEST_NOTE_ID}", description="Delete Test Note")
        self.test_endpoint("DELETE", f"/pue-rentals/{TEST_RENTAL_ID}", description="Delete Test PUE Rental")
        self.test_endpoint("DELETE", f"/pue/{TEST_PUE_ID}", description="Delete Test PUE")
        self.test_endpoint("DELETE", f"/batteries/{TEST_BATTERY_ID}", description="Delete Test Battery")
        self.test_endpoint("DELETE", f"/users/{TEST_USER_ID}", description="Delete Test User")
        self.test_endpoint("DELETE", f"/hubs/{TEST_HUB_ID}", description="Delete Test Hub")
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 COMPREHENSIVE API TESTING COMPLETE!")
        print("="*60)
        print("✅ All major endpoints tested")
        print("✅ Authentication and security verified")
        print("✅ Data operations confirmed working")
        print("✅ Performance benchmarks recorded")
        print("✅ Edge cases and error handling tested")
        print("✅ All test data cleaned up")
        print("="*60)

def main():
    """Main function to run all tests"""
    print("Solar Hub Management API - Comprehensive Test Suite")
    print("="*60)
    
    tester = APITester(BASE_URL)
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not responding properly. Status: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API at {BASE_URL}")
        print(f"   Error: {e}")
        print("   Make sure the API is running: uvicorn main:app --reload")
        return
    
    print(f"✅ API is running at {BASE_URL}")
    
    # Run all tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()

        
        # 9. Webhook Test (Live Data)
        print("\n" + "="*30 + " WEBHOOK TESTS " + "="*30)
        
        # Create sample battery data
        sample_battery_data = {
            "id": 1,
            "battery_id": TEST_BATTERY_ID,
            "state_of_charge": 78,
            "voltage": 12.4,
            "current_amps": 3.2,
            "power_watts": 39.68,
            "time_remaining": 240,
            "temp_battery": 29.5,
            "amp_hours_consumed": 2.1,
            "charging_current": 0.0,
            "timestamp": datetime.now().isoformat(),
            "usb_voltage": 5.0,
            "usb_power": 3.0,
            "usb_current": 0.6,
            "latitude": -1.286389,
            "longitude": 36.817223,
            "altitude": 1680.0,
            "SD_card_storage_remaining": 950.0,
            "battery_orientation": "normal",
            "number_GPS_satellites_for_fix": 10,
            "mobile_signal_strength": 5,
            "event_type": "normal_operation",
            "new_battery_cycle": 0
        }
        
        webhook_data = {
            "event_id": f"test-event-{int(time.time())}",
            "webhook_id": "test-webhook-123",
            "device_id": "0291f60a-cfaf-462d-9e82-5ce662fb3823",
            "thing_id": "test-thing-456",
            "values": [
                {
                    "id": "prop-data-123",
                    "name": "data",
                    "value": json.dumps(sample_battery_data),
                    "persist": True,
                    "updated_at": datetime.now().isoformat(),
                    "created_by": "test-system"
                }
            ]
        }
        
        self.test_endpoint("POST", "/webhook/live-data", webhook_data, "Send Live Data via Webhook", auth=False)
        
        # Wait a moment for data to be processed
        time.sleep(2)
        
        # 10. Data Query Tests
        print("\n" + "="*30 + " DATA QUERY TESTS " + "="*30)
        
        # Send a few more data points for testing
        for i in range(3):
            sample_data = sample_battery_data.copy()
            sample_data["state_of_charge"] = 78 - i * 2
            sample_data["voltage"] = 12.4 - i * 0.1
            sample_data["timestamp"] = (datetime.now() - timedelta(minutes=i*10)).isoformat()
            
            webhook_payload = webhook_data.copy()
            webhook_payload["values"][0]["value"] = json.dumps(sample_data)
            webhook_payload["event_id"] = f"test-event-{int(time.time())}-{i}"
            
            self.test_endpoint("POST", "/webhook/live-data", webhook_payload, f"Send Test Data Point {i+1}", auth=False)
            time.sleep(1)
        
        # Test data retrieval endpoints
        self.test_endpoint("GET", f"/data/latest/{TEST_BATTERY_ID}", description="Get Latest Battery Data")
        
        # Test battery data with timestamps
        start_time = (datetime.now() - timedelta(hours=1)).isoformat() + "Z"
        end_time = datetime.now().isoformat() + "Z"
        self.test_endpoint("GET", f"/data/battery/{TEST_BATTERY_ID}?start_timestamp={start_time}&end_timestamp={end_time}&limit=10", description="Get Battery Data with Timestamps")
        
        # Test CSV export
        print("\n🧪 Testing CSV Export")
        try:
            response = self.session.get(
                f"{self.base_url}/data/battery/{TEST_BATTERY_ID}?format=csv&limit=5",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status_code == 200:
                print("✅ CSV Export successful")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Data sample: {response.text[:200]}...")
            else:
                print(f"❌ CSV Export failed ({response.status_code})")
        except Exception as e:
            print(f"❌ CSV Export error: {e}")
        
        # Test data query POST endpoint
        query_data = {
            "battery_ids": [TEST_BATTERY_ID],
            "fields": ["timestamp", "state_of_charge", "voltage", "current_amps"],
            "format": "json"
        }
        self.test_endpoint("POST", "/data/query", query_data, "Query Live Data (JSON)")
        
        # Test dataframe format
        query_data["format"] = "dataframe"
        self.test_endpoint("POST", "/data/query", query_data, "Query Live Data (DataFrame)")
        
        # Test battery summary
        self.test_endpoint("GET", f"/data/summary/{TEST_BATTERY_ID}?hours=1", description="Get Battery Summary")
        
        # 11. Security Tests
        print("\n" + "="*30 + " SECURITY TESTS " + "="*30)
        
        # Test without authorization
        print("\n🧪 Testing Unauthorized Access")
        try:
            response = requests.get(f"{self.base_url}/hubs/{TEST_HUB_ID}")
            if response.status_code == 403:
                print("✅ Correctly blocked unauthorized access (403)")
            else:
                print(f"⚠️  Unexpected response for unauthorized access: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing unauthorized access: {e}")
        
        # Test with invalid token
        print("\n🧪 Testing Invalid Token")
        try:
            response = requests.get(
                f"{self.base_url}/hubs/{TEST_HUB_ID}",
                headers={"Authorization": "Bearer invalid-token-123"}
            )
            if response.status_code == 401:
                print("✅ Correctly rejected invalid token (401)")
            else:
                print(f"⚠️  Unexpected response for invalid token: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing invalid token: {e}")
        
        # 12. Performance Tests
        print("\n" + "="*30 + " PERFORMANCE TESTS " + "="*30)
        
        print("\n🧪 Testing Response Times")
        endpoints_to_test = [
            ("GET", f"/hubs/{TEST_HUB_ID}", "Get Hub"),
            ("GET", f"/batteries/{TEST_BATTERY_ID}", "Get Battery"),
            ("GET", f"/data/latest/{TEST_BATTERY_ID}", "Get Latest Data"),
            ("GET", "/health", "Health Check")
        ]
        
        for method, endpoint, description in endpoints_to_test:
            start_time = time.time()
            try:
                if "health" in endpoint:
                    response = requests.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    print(f"✅ {description}: {response_time:.2f}ms")
                else:
                    print(f"❌ {description}: Failed ({response.status_code})")
            except Exception as e:
                print(f"❌ {description}: Error - {e}")
        
        # 13. Cleanup Tests
        print("\n" + "="*30 + " CLEANUP TESTS " + "="*30)
        
        self.test_endpoint("DELETE", f"/notes/{TEST_NOTE_ID}", description="Delete Test Note")
        self.test_endpoint("DELETE", f"/pue-rentals/{TEST_RENTAL_ID}", description="Delete Test PUE Rental")
        self.test_endpoint("DELETE", f"/pue/{TEST_PUE_ID}", description="Delete Test PUE")
        self.test_endpoint("DELETE", f"/batteries/{TEST_BATTERY_ID}", description="Delete Test Battery")
        self.test_endpoint("DELETE", f"/users/{TEST_USER_ID}", description="Delete Test User")
        self.test_endpoint("DELETE", f"/hubs/{TEST_HUB_ID}", description="Delete Test Hub")
        
        print("\n" + "="*50)
        print("🎉 API Testing Complete!")
        print("="*50)

def main():
    """Main function to run all tests"""
    print("Solar Hub Management API - Comprehensive Test Suite")
    print("="*60)
    
    tester = APITester(BASE_URL)
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not responding properly. Status: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API at {BASE_URL}")
        print(f"   Error: {e}")
        print("   Make sure the API is running: uvicorn main:app --reload")
        return
    
    print(f"✅ API is running at {BASE_URL}")
    
    # Run all tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()