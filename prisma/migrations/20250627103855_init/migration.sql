-- CreateTable
CREATE TABLE "SolarHub" (
    "hub_id" BIGINT NOT NULL,
    "what_three_word_location" VARCHAR(255),
    "solar_capacity_kw" BIGINT,
    "country" VARCHAR(255),
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,

    CONSTRAINT "SolarHub_pkey" PRIMARY KEY ("hub_id")
);

-- CreateTable
CREATE TABLE "User" (
    "user_id" BIGINT NOT NULL,
    "Name" VARCHAR(255) NOT NULL,
    "users_identification_document_number" TEXT,
    "mobile_number" VARCHAR(255),
    "address" TEXT,
    "hub_id" BIGINT NOT NULL,
    "user_access_level" VARCHAR(255) NOT NULL,
    "username" VARCHAR(255) NOT NULL,
    "password_hash" VARCHAR(255) NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("user_id")
);

-- CreateTable
CREATE TABLE "Note" (
    "id" BIGINT NOT NULL,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Note_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BEPPPBattery_Notes" (
    "battery_id" BIGINT NOT NULL,
    "note_id" BIGINT NOT NULL,

    CONSTRAINT "BEPPPBattery_Notes_pkey" PRIMARY KEY ("battery_id","note_id")
);

-- CreateTable
CREATE TABLE "Rental_Notes" (
    "rental_id" BIGINT NOT NULL,
    "note_id" BIGINT NOT NULL,

    CONSTRAINT "Rental_Notes_pkey" PRIMARY KEY ("rental_id","note_id")
);

-- CreateTable
CREATE TABLE "PUE_Notes" (
    "pue_id" BIGINT NOT NULL,
    "note_id" BIGINT NOT NULL,

    CONSTRAINT "PUE_Notes_pkey" PRIMARY KEY ("pue_id","note_id")
);

-- CreateTable
CREATE TABLE "PUERental_Notes" (
    "pue_rental_id" BIGINT NOT NULL,
    "note_id" BIGINT NOT NULL,

    CONSTRAINT "PUERental_Notes_pkey" PRIMARY KEY ("pue_rental_id","note_id")
);

-- CreateTable
CREATE TABLE "BEPPPBattery" (
    "battery_id" BIGINT NOT NULL,
    "hub_id" BIGINT NOT NULL,
    "battery_capacity_wh" BIGINT,
    "status" TEXT DEFAULT 'available',

    CONSTRAINT "BEPPPBattery_pkey" PRIMARY KEY ("battery_id")
);

-- CreateTable
CREATE TABLE "LiveData" (
    "id" BIGINT NOT NULL,
    "battery_id" BIGINT NOT NULL,
    "state_of_charge" BIGINT,
    "voltage" DOUBLE PRECISION,
    "current_amps" DOUBLE PRECISION,
    "power_watts" DOUBLE PRECISION,
    "time_remaining" BIGINT,
    "temp_battery" DOUBLE PRECISION,
    "amp_hours_consumed" DOUBLE PRECISION,
    "charging_current" DOUBLE PRECISION,
    "timestamp" TIMESTAMP(0),
    "usb_voltage" DOUBLE PRECISION,
    "usb_power" DOUBLE PRECISION,
    "usb_current" DOUBLE PRECISION,
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,
    "altitude" DOUBLE PRECISION,
    "SD_card_storage_remaining" DOUBLE PRECISION,
    "battery_orientation" VARCHAR(255),
    "number_GPS_satellites_for_fix" INTEGER,
    "mobile_signal_strength" INTEGER,
    "event_type" VARCHAR(255),
    "new_battery_cycle" INTEGER,

    CONSTRAINT "LiveData_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Rental" (
    "rentral_id" BIGINT NOT NULL,
    "battery_id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "timestamp_taken" TIMESTAMP(0) NOT NULL,
    "due_back" TIMESTAMP(0),
    "date_returned" TIMESTAMP(0),

    CONSTRAINT "Rental_pkey" PRIMARY KEY ("rentral_id")
);

-- CreateTable
CREATE TABLE "ProductiveUseEquipment" (
    "pue_id" BIGINT NOT NULL,
    "hub_id" BIGINT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "rental_cost" DOUBLE PRECISION,
    "status" TEXT DEFAULT 'available',
    "rental_count" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "ProductiveUseEquipment_pkey" PRIMARY KEY ("pue_id")
);

-- CreateTable
CREATE TABLE "PUERental" (
    "pue_rental_id" BIGINT NOT NULL,
    "pue_id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "timestamp_taken" TIMESTAMP(0) NOT NULL,
    "due_back" TIMESTAMP(0),
    "date_returned" TIMESTAMP(0),

    CONSTRAINT "PUERental_pkey" PRIMARY KEY ("pue_rental_id")
);

-- CreateTable
CREATE TABLE "BatteryPUERental" (
    "battery_rental_id" BIGINT NOT NULL,
    "pue_rental_id" BIGINT NOT NULL,

    CONSTRAINT "BatteryPUERental_pkey" PRIMARY KEY ("battery_rental_id","pue_rental_id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_username_key" ON "User"("username");

-- AddForeignKey
ALTER TABLE "User" ADD CONSTRAINT "User_hub_id_fkey" FOREIGN KEY ("hub_id") REFERENCES "SolarHub"("hub_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BEPPPBattery_Notes" ADD CONSTRAINT "BEPPPBattery_Notes_battery_id_fkey" FOREIGN KEY ("battery_id") REFERENCES "BEPPPBattery"("battery_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BEPPPBattery_Notes" ADD CONSTRAINT "BEPPPBattery_Notes_note_id_fkey" FOREIGN KEY ("note_id") REFERENCES "Note"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Rental_Notes" ADD CONSTRAINT "Rental_Notes_rental_id_fkey" FOREIGN KEY ("rental_id") REFERENCES "Rental"("rentral_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Rental_Notes" ADD CONSTRAINT "Rental_Notes_note_id_fkey" FOREIGN KEY ("note_id") REFERENCES "Note"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PUE_Notes" ADD CONSTRAINT "PUE_Notes_pue_id_fkey" FOREIGN KEY ("pue_id") REFERENCES "ProductiveUseEquipment"("pue_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PUE_Notes" ADD CONSTRAINT "PUE_Notes_note_id_fkey" FOREIGN KEY ("note_id") REFERENCES "Note"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PUERental_Notes" ADD CONSTRAINT "PUERental_Notes_pue_rental_id_fkey" FOREIGN KEY ("pue_rental_id") REFERENCES "PUERental"("pue_rental_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PUERental_Notes" ADD CONSTRAINT "PUERental_Notes_note_id_fkey" FOREIGN KEY ("note_id") REFERENCES "Note"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BEPPPBattery" ADD CONSTRAINT "BEPPPBattery_hub_id_fkey" FOREIGN KEY ("hub_id") REFERENCES "SolarHub"("hub_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LiveData" ADD CONSTRAINT "LiveData_battery_id_fkey" FOREIGN KEY ("battery_id") REFERENCES "BEPPPBattery"("battery_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Rental" ADD CONSTRAINT "Rental_battery_id_fkey" FOREIGN KEY ("battery_id") REFERENCES "BEPPPBattery"("battery_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Rental" ADD CONSTRAINT "Rental_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("user_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProductiveUseEquipment" ADD CONSTRAINT "ProductiveUseEquipment_hub_id_fkey" FOREIGN KEY ("hub_id") REFERENCES "SolarHub"("hub_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PUERental" ADD CONSTRAINT "PUERental_pue_id_fkey" FOREIGN KEY ("pue_id") REFERENCES "ProductiveUseEquipment"("pue_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PUERental" ADD CONSTRAINT "PUERental_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "User"("user_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BatteryPUERental" ADD CONSTRAINT "BatteryPUERental_battery_rental_id_fkey" FOREIGN KEY ("battery_rental_id") REFERENCES "Rental"("rentral_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BatteryPUERental" ADD CONSTRAINT "BatteryPUERental_pue_rental_id_fkey" FOREIGN KEY ("pue_rental_id") REFERENCES "PUERental"("pue_rental_id") ON DELETE RESTRICT ON UPDATE CASCADE;
