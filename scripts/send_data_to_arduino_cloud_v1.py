import time
import random
import datetime
import json
from arduino_iot_cloud import ArduinoCloudClient

# Arduino Cloud credentials
DEVICE_ID = "0291f60a-cfaf-462d-9e82-5ce662fb3823"
SECRET_KEY = "llXRFeQyYtfm!EXXIIvXygwmD"

# Initial battery state with all required fields
battery_state = {
    "id": 1,
    "battery_id": 1,
    "state_of_charge": 80.0,
    "voltage": 11.5,
    "current_amps": 1.5,
    "power_watts": 17.25,
    "time_remaining": 240,
    "temp_battery": 25.0,
    "amp_hours_consumed": 0.0,
    "charging_current": 0.0,
    "timestamp": int(time.time()),
    "usb_voltage": 5.0,
    "usb_power": 2.5,
    "usb_current": 0.5,
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude": 15.0,
    "SD_card_storage_remaining": 1024.0,
    "battery_orientation": "normal",
    "number_GPS_satellites_for_fix": 8,
    "mobile_signal_strength": 3,
    "event_type": "normal_operation",
    "new_battery_cycle": 0
}

def clamp(val, min_val, max_val):
    return max(min_val, min(max_val, val))

def update_battery_state(state):
    # Update timestamp
    state["timestamp"] = int(time.time())
    
    # Simulate state of charge change (decrease if not charging, increase if charging)
    is_charging = random.random() < 0.3  # 30% chance of charging
    
    if is_charging:
        charge_change = random.uniform(0.1, 0.5)
        state["charging_current"] = random.uniform(1.0, 3.0)
    else:
        charge_change = random.uniform(-0.5, -0.1)
        state["charging_current"] = 0.0
    
    state["state_of_charge"] = clamp(state["state_of_charge"] + charge_change, 0, 100)
    
    # Update voltage based on state of charge
    base_voltage = 8 + (state["state_of_charge"] / 100) * 4
    state["voltage"] = clamp(base_voltage + random.uniform(-0.1, 0.1), 8, 12)
    
    # Update current draw
    state["current_amps"] = random.uniform(0, 5)
    
    # Calculate power
    state["power_watts"] = state["voltage"] * state["current_amps"]
    
    # Update time remaining (based on charge level and current draw)
    if state["current_amps"] > 0:
        # Assuming a 50Ah battery
        capacity_remaining = 50 * (state["state_of_charge"] / 100)
        hours_remaining = capacity_remaining / state["current_amps"]
        state["time_remaining"] = int(hours_remaining * 60)  # Convert to minutes
    else:
        state["time_remaining"] = 0
    
    # Update amp hours consumed (incremental)
    time_fraction = 30 / 3600  # 30 seconds in hours
    state["amp_hours_consumed"] += state["current_amps"] * time_fraction
    
    # Update temperature (random fluctuation)
    state["temp_battery"] = clamp(state["temp_battery"] + random.uniform(-0.5, 0.5), 15, 45)
    
    # Update USB-related metrics
    state["usb_voltage"] = clamp(5.0 + random.uniform(-0.2, 0.2), 4.8, 5.2)
    state["usb_current"] = clamp(state["usb_current"] + random.uniform(-0.1, 0.1), 0, 2.0)
    state["usb_power"] = state["usb_voltage"] * state["usb_current"]
    
    # Simulate slight GPS drift
    state["latitude"] += random.uniform(-0.0001, 0.0001)
    state["longitude"] += random.uniform(-0.0001, 0.0001)
    state["altitude"] += random.uniform(-0.1, 0.1)
    
    # Update storage
    state["SD_card_storage_remaining"] -= random.uniform(0, 0.5)  # Lose up to 0.5 MB
    
    # Randomly change orientation sometimes
    if random.random() < 0.05:  # 5% chance
        orientations = ["normal", "upside_down", "sideways", "tilted"]
        state["battery_orientation"] = random.choice(orientations)
    
    # Update GPS satellites (fluctuates)
    state["number_GPS_satellites_for_fix"] = clamp(
        state["number_GPS_satellites_for_fix"] + random.choice([-1, 0, 0, 0, 1]), 
        4, 12
    )
    
    # Update mobile signal (fluctuates)
    state["mobile_signal_strength"] = clamp(
        state["mobile_signal_strength"] + random.choice([-1, 0, 0, 1]), 
        0, 5
    )
    
    # Occasionally change event type
    if random.random() < 0.05:  # 5% chance
        events = ["normal_operation", "low_battery", "charging", "discharging", "error", "warning"]
        state["event_type"] = random.choice(events)
    
    # Very rarely start a new battery cycle
    if random.random() < 0.01:  # 1% chance
        state["new_battery_cycle"] = 1
    else:
        state["new_battery_cycle"] = 0
    
    return state

# Optional callback function for cloud updates
def on_data_changed(client, value):
    print(f"Cloud updated data to: {value}")

def send_to_arduino_cloud(client, state):
    try:
        # Format timestamp for better readability
        state_copy = state.copy()
        timestamp_unix = state_copy["timestamp"]
        state_copy["timestamp"] = datetime.datetime.fromtimestamp(timestamp_unix).isoformat()
        
        # Convert entire state to JSON string
        json_string = json.dumps(state_copy)
        
        print(f"Attempting to send JSON string: {json_string[:200]}...")  # Show first 200 chars
        print(f"JSON length: {len(json_string)} characters")
        
        # Send the JSON string to the 'data' property
        client["data"] = json_string
        
        # Process the update immediately in sync mode
        client.update()
        
        print(f"Data successfully sent to Arduino Cloud")
        print(f"SoC: {state['state_of_charge']:.1f}%, Voltage: {state['voltage']:.2f}V, " +
              f"Current: {state['current_amps']:.2f}A, Power: {state['power_watts']:.2f}W")
        
        # Try to read back the value to confirm it was set
        try:
            current_value = client["data"]
            print(f"Confirmed: property 'data' now contains: {len(str(current_value))} characters")
        except Exception as read_error:
            print(f"Could not read back 'data' property: {read_error}")
        
    except Exception as e:
        print(f"Error sending data: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("Starting battery monitoring simulation...")
    print(f"Device ID: {DEVICE_ID}")
    
    # Initialize the ArduinoCloudClient in synchronous mode
    client = ArduinoCloudClient(
        device_id=DEVICE_ID, 
        username=DEVICE_ID, 
        password=SECRET_KEY,
        sync_mode=True
    )
    
    # Start the client first
    try:
        client.start()
        print("Successfully connected to Arduino Cloud")
        
    except Exception as e:
        print(f"Failed to connect to Arduino Cloud: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Register the property AFTER starting the client
    try:
        client.register("data", value="")
        print("Property 'data' registered successfully")
        
        # Update to process the registration
        client.update()
        
    except Exception as e:
        print(f"Error registering property: {e}")
        import traceback
        traceback.print_exc()
        return
    
    state = battery_state.copy()
    
    try:
        while True:
            state = update_battery_state(state)
            send_to_arduino_cloud(client, state)
            
            time.sleep(30)  # Send data every 30 seconds
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error in main loop: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always stop the client properly
        try:
            client.stop()
            print("Disconnected from Arduino Cloud")
        except Exception as e:
            print(f"Error stopping client: {e}")

if __name__ == "__main__":
    main()