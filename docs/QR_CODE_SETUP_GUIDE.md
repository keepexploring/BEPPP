# QR Code System - Complete Setup Guide

## Overview

The QR code system enables fast rental operations by scanning user cards and battery labels. This guide covers both backend and frontend implementation.

## System Features

### ✅ User Cards
- **Short ID Format**: `BH-0001`, `BH-0002`, etc.
- **QR Code Contains**: User ID, username, short ID
- **Card Design**: Credit card size (85.6mm x 53.98mm)
- **Downloadable**: PDF format for printing

### ✅ Battery Labels
- **Short ID Format**: `BAT-0001`, `BAT-0002`, etc.
- **QR Code Contains**: Battery ID, serial number, short ID
- **Label Design**: Printable sticker format
- **Downloadable**: PDF format for printing

### ✅ Rental Workflow
1. Scan user QR code → Auto-fills customer info
2. Scan battery QR code → Auto-fills battery selection
3. Set rental terms → Create rental

### ✅ Hub-Based Permissions
- **Superadmins**: See all hubs, select any hub
- **Hub Managers**: See only their hubs, auto-select if one hub
- **Users**: See only their hubs

## Frontend Implementation

### 1. Dependencies Added

```json
{
  "dependencies": {
    "qrcode": "^1.5.3",           // QR code generation
    "jspdf": "^2.5.1",             // PDF generation
    "html5-qrcode": "^2.3.8"       // QR code scanning
  }
}
```

### 2. Files Created

```
frontend/src/
├── composables/
│   └── useQRCode.js              // QR utilities
├── components/
│   ├── QRScanner.vue             // Camera-based scanner
│   └── UserSearch.vue            // Search fallback
└── pages/
    ├── RentalsPageWithQR.vue     // Updated rentals with QR
    ├── UsersPageWithQR.vue       // Users with card download
    └── BatteriesPageWithQR.vue   // Batteries with label download
```

### 3. QR Code Utilities (`useQRCode.js`)

**Functions Available**:
```javascript
import {
  generateUserShortId,      // BH-0001 format
  generateQRCode,            // Generate QR image
  generateUserCardPDF,       // Create printable card
  downloadUserCard,          // Download single card
  generateBulkUserCards,     // Print multiple cards
  parseQRData               // Parse scanned QR
} from 'src/composables/useQRCode'
```

**Usage Example**:
```javascript
// Generate and download user card
import { downloadUserCard } from 'src/composables/useQRCode'

const handleDownloadCard = async (user) => {
  await downloadUserCard(user)
}
```

### 4. QR Scanner Component

```vue
<template>
  <QRScanner
    @scanned="handleScan"
    button-label="Scan QR Code"
    manual-label="Or enter ID manually"
    :show-manual-entry="true"
  />
</template>

<script setup>
import QRScanner from 'src/components/QRScanner.vue'

const handleScan = (qrData) => {
  console.log('Scanned:', qrData)
  // Process the QR data
}
</script>
```

### 5. User Search Component

```vue
<template>
  <UserSearch
    :users="userList"
    v-model="selectedUser"
    @select="handleUserSelect"
  />
</template>

<script setup>
import UserSearch from 'src/components/UserSearch.vue'

const userList = ref([])
const selectedUser = ref(null)

const handleUserSelect = (user) => {
  console.log('Selected user:', user)
}
</script>
```

## Backend Implementation

### Required Database Changes

**Migration file**: `add_short_id_fields`

```sql
-- Add short_id to users
ALTER TABLE users ADD COLUMN short_id VARCHAR(20) UNIQUE;
CREATE INDEX idx_users_short_id ON users(short_id);

-- Add short_id to batteries
ALTER TABLE batteries ADD COLUMN short_id VARCHAR(20) UNIQUE;
CREATE INDEX idx_batteries_short_id ON batteries(short_id);

-- Backfill existing data
UPDATE users SET short_id = 'BH-' || LPAD(id::TEXT, 4, '0');
UPDATE batteries SET short_id = 'BAT-' || LPAD(id::TEXT, 4, '0');
```

### API Endpoints to Add

#### 1. User Lookup by Short ID

```python
@app.get("/users/by-short-id/{short_id}")
async def get_user_by_short_id(
    short_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Look up user by their short ID from QR code"""
    user = db.query(User).filter(User.short_id == short_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

#### 2. Battery Lookup by Short ID

```python
@app.get("/batteries/by-short-id/{short_id}")
async def get_battery_by_short_id(
    short_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Look up battery by their short ID from QR code"""
    battery = db.query(Battery).filter(Battery.short_id == short_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    return battery
```

#### 3. Updated User Creation

```python
@app.post("/users/")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # ... existing validation ...

    db_user = User(**user.dict(exclude={'password'}))
    db_user.hashed_password = pwd_context.hash(user.password)

    db.add(db_user)
    db.flush()  # Get ID before commit

    # Generate short ID
    db_user.short_id = f"BH-{str(db_user.id).zfill(4)}"

    db.commit()
    db.refresh(db_user)

    return db_user
```

#### 4. Updated Battery Creation

```python
@app.post("/batteries/")
async def create_battery(battery: BatteryCreate, db: Session = Depends(get_db)):
    # ... existing validation ...

    db_battery = Battery(**battery.dict())
    db.add(db_battery)
    db.flush()

    # Generate short ID
    db_battery.short_id = f"BAT-{str(db_battery.id).zfill(4)}"

    db.commit()
    db.refresh(db_battery)

    return db_battery
```

#### 5. Hub Access Control

```python
@app.get("/hubs/")
async def list_hubs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List hubs based on user role:
    - Superadmin: All hubs
    - Others: Only hubs with access
    """
    if current_user.role == "superadmin":
        return db.query(Hub).all()
    else:
        # Get user's assigned hubs
        return db.query(Hub).join(
            UserHubAccess,
            Hub.id == UserHubAccess.hub_id
        ).filter(
            UserHubAccess.user_id == current_user.id
        ).all()
```

## QR Code Data Format

### User QR Code
```json
{
  "type": "user",
  "id": "BH-0001",
  "user_id": 1,
  "username": "john_doe"
}
```

### Battery QR Code
```json
{
  "type": "battery",
  "id": "BAT-0023",
  "battery_id": 23,
  "serial_number": "SN123456",
  "hub_id": 1
}
```

## Rental Workflow with QR Codes

### Step-by-Step Process

1. **Hub Selection** (Superadmin only)
   - Auto-selected for hub managers
   - Shows only accessible hubs

2. **Customer Selection**
   - Option A: Scan user QR code
   - Option B: Search by name/ID
   - Option C: Manual ID entry
   - Displays selected customer info

3. **Battery Selection**
   - Option A: Scan battery QR code
   - Option B: Select from dropdown
   - Option C: Manual ID entry
   - Shows only available batteries

4. **Rental Details**
   - Set dates and rates
   - Add optional equipment
   - Confirm and create

## User Card Design

### Card Specifications

- **Size**: 85.6mm × 53.98mm (credit card size)
- **Material**: PVC or cardstock
- **Orientation**: Landscape
- **Colors**: Primary blue header, white body

### Card Layout

```
┌─────────────────────────────────────┐
│  Battery Hub - Rental Card          │ (Blue header)
├─────────────────────────────────────┤
│  John Doe                    [QR]   │
│  ID: BH-0001                 [QR]   │
│  User: john_doe              [QR]   │
│  john@example.com            [QR]   │
│                                     │
│  Scan QR code to start rental       │
└─────────────────────────────────────┘
```

## Battery Label Design

### Label Specifications

- **Size**: 50mm × 30mm (sticker format)
- **Material**: Weatherproof vinyl
- **Orientation**: Landscape

### Label Layout

```
┌──────────────────────────┐
│ Battery: BAT-0023        │
│ SN: SN123456     [QR]    │
│ 5000Wh          [QR]    │
└──────────────────────────┘
```

## Printing Instructions

### For Users Cards

1. **Single Card**:
   ```javascript
   // In UsersPage.vue
   await downloadUserCard(user)
   // Downloads: battery-hub-card-BH-0001.pdf
   ```

2. **Bulk Cards** (Print multiple users):
   ```javascript
   const selectedUsers = [user1, user2, user3]
   const pdf = await generateBulkUserCards(selectedUsers)
   pdf.save('user-cards-batch.pdf')
   // Prints 6 cards per A4 page
   ```

3. **Physical Printing**:
   - Use PVC card printer (CR80 size)
   - Or print on cardstock and laminate
   - Recommended: Zebra, Evolis, or Fargo card printers

### For Battery Labels

1. **Label Generation**:
   ```javascript
   await downloadBatteryLabel(battery)
   ```

2. **Physical Printing**:
   - Use label printer (e.g., Dymo, Brother)
   - Weatherproof vinyl labels recommended
   - Size: 2" × 1.25" (50mm × 30mm)

## Camera Permissions

### Mobile Setup

**iOS**:
- Settings → Safari → Camera → Allow
- Or prompt appears on first scan

**Android**:
- Settings → Apps → Browser → Permissions → Camera → Allow
- Or prompt appears on first scan

### Desktop Setup

**Chrome/Edge**:
- Allow camera access when prompted
- Site settings → Camera → Allow

**Firefox**:
- Permissions tab → Camera → Allow

## Testing the QR System

### 1. Generate Test User Card

```bash
# In browser console (Users page)
const testUser = {
  id: 1,
  username: "test_user",
  full_name: "Test User",
  email: "test@example.com",
  short_id: "BH-0001"
}

import { downloadUserCard } from 'src/composables/useQRCode'
await downloadUserCard(testUser)
```

### 2. Test QR Scanner

1. Open Rentals page
2. Click "New Rental"
3. Select hub
4. Click "Scan User QR Code"
5. Allow camera access
6. Point camera at printed QR code
7. Verify user is auto-selected

### 3. Manual Entry Testing

1. In rental dialog, customer step
2. Enter "BH-0001" in manual input
3. Verify user lookup works

## Troubleshooting

### QR Code Won't Scan

**Issue**: Camera not detecting QR code
**Solutions**:
- Ensure good lighting
- Hold steady for 2-3 seconds
- Try manual ID entry
- Check camera permissions
- Clean camera lens

### Invalid QR Code Error

**Issue**: QR code scanned but not recognized
**Solutions**:
- Verify QR code format matches spec
- Regenerate user card
- Check backend short_id exists
- Try manual ID entry

### Camera Permission Denied

**Issue**: Browser blocks camera access
**Solutions**:
- Check browser settings
- Use HTTPS (required for camera in many browsers)
- Try different browser
- Check device permissions

## Production Checklist

### Before Deployment

- [ ] Backend migration applied
- [ ] Short IDs generated for existing users/batteries
- [ ] QR lookup endpoints tested
- [ ] Camera permissions work on target devices
- [ ] Cards printed and tested
- [ ] Battery labels printed and tested
- [ ] Hub access control verified
- [ ] Mobile devices tested (iOS & Android)
- [ ] Manual entry fallback tested

### After Deployment

- [ ] Train staff on QR scanning
- [ ] Print user cards for existing customers
- [ ] Label all batteries
- [ ] Test rental workflow end-to-end
- [ ] Monitor error rates
- [ ] Gather user feedback

## Benefits

1. **Speed**: Rentals created in 30 seconds vs 3-5 minutes
2. **Accuracy**: No typos, auto-filled data
3. **User Experience**: Modern, contactless
4. **Scalability**: Works with thousands of users
5. **Offline Capable**: Manual ID entry fallback

## Future Enhancements

- [ ] NFC card support
- [ ] Barcode scanning fallback
- [ ] Bulk card generation UI
- [ ] Card expiration dates
- [ ] Photo on cards
- [ ] Customer self-service kiosk mode
- [ ] Mobile app for scanning
