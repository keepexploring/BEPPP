#!/usr/bin/env python3
"""
Battery Data Submission Example
Demonstrates how to authenticate and submit battery data to BEPPP Cloud API
"""

import requests
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class BatteryDataClient:
    def __init__(self, base_url: str = "https://data.beppp.cloud"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        
    def authenticate_battery(self, battery_id: int, battery_secret: str) -> bool:
        """
        Authenticate battery and get access token
        
        Args:
            battery_id: The battery ID
            battery_secret: The battery secret key
            
        Returns:
            True if authentication successful, False otherwise
        """
        auth_url = f"{self.base_url}/auth/battery-login"
        
        auth_data = {
            "battery_id": battery_id,
            "battery_secret": battery_secret
        }
        
        try:
            response = self.session.post(
                auth_url,
                headers={"Content-Type": "application/json"},
                json=auth_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                print(f"Authentication successful for battery {battery_id}")
                print(f"Token expires in {token_data.get('expires_in_hours', 'unknown')} hours")
                return True
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"Authentication error: {e}")
            return False
    
    def submit_battery_data(self, battery_data: Dict[str, Any]) -> bool:
        """
        Submit battery data to the webhook endpoint
        
        Args:
            battery_data: Dictionary containing battery metrics
            
        Returns:
            True if submission successful, False otherwise
        """
        if not self.access_token:
            print("Error: Not authenticated. Call authenticate_battery() first.")
            return False
            
        webhook_url = f"{self.base_url}/webhook/live-data"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.post(
                webhook_url,
                headers=headers,
                json=battery_data
            )
            
            if response.status_code in [200, 201]:
                print("Battery data submitted successfully")
                return True
            else:
                print(f"Data submission failed: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"Data submission error: {e}")
            return False

def create_sample_battery_data(battery_id: int, 
                             state_of_charge: float = 75.0,
                             voltage: float = 12.8,
                             current_amps: float = 1.5,
                             temp_battery: float = 22.5,
                             latitude: float = -1.286389,
                             longitude: float = 36.817223,
                             altitude: float = 1680.0,
                             usb_voltage: float = 5.0,
                             usb_current: float = 0.8) -> Dict[str, Any]:
    """
    Create sample battery data with current timestamp
    
    Args:
        battery_id: The battery ID
        Additional parameters for battery metrics
        
    Returns:
        Dictionary with battery data
    """
    power_watts = voltage * current_amps
    usb_power = usb_voltage * usb_current
    
    return {
        "battery_id": battery_id,
        "state_of_charge": state_of_charge,
        "voltage": voltage,
        "current_amps": current_amps,
        "power_watts": round(power_watts, 2),
        "temp_battery": temp_battery,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "usb_voltage": usb_voltage,
        "usb_current": usb_current,
        "usb_power": round(usb_power, 2)
    }

def main():
    """
    Main example demonstrating battery authentication and data submission
    """
    # Configuration
    BATTERY_ID = 1
    BATTERY_SECRET = "QAIVBOZf3z0nYo-TXVsc2SP2Gf1aI7eRDY_RxY3tEYo"
    
    # Initialize client
    client = BatteryDataClient()
    
    # Step 1: Authenticate
    print("Step 1: Authenticating battery...")
    if not client.authenticate_battery(BATTERY_ID, BATTERY_SECRET):
        print("Authentication failed. Exiting.")
        return
    
    # Step 2: Create sample data
    print("\nStep 2: Creating battery data...")
    battery_data = create_sample_battery_data(
        battery_id=BATTERY_ID,
        state_of_charge=75.0,
        voltage=12.8,
        current_amps=1.5,
        temp_battery=22.5
    )
    
    print("Battery data to submit:")
    print(json.dumps(battery_data, indent=2))
    
    # Step 3: Submit data
    print("\nStep 3: Submitting battery data...")
    if client.submit_battery_data(battery_data):
        print("✓ Battery data submission completed successfully")
    else:
        print("✗ Battery data submission failed")

if __name__ == "__main__":
    main()