# Failed Geocoding Attempts

This document tracks stores that failed to geocode automatically and need manual review.

## Paknsave (7 stores)

Geocoding attempted: 2026-01-02
Success rate: 87.7% (50/57)

### Failed Stores

1. **PAK'nSAVE Hastings**
   - Address: `602 Heretaunga Street West, West End Shopping Centre, Hastings, 4120`
   - API ID: `b39562a4-2b72-43fe-b9ba-eda1d651ad0b`
   - Issue: Shopping centre name may be confusing geocoder

2. **PAK'nSAVE Kapiti**
   - Address: `76 Rimu Road, Paraparaumu, 5032`
   - API ID: `c180a72d-5dbe-4403-b7c7-91655e505492`
   - Issue: Unknown

3. **PAK'nSAVE Manukau**
   - Address: `6 Cavendish Drive, Manukau City, Auckland, 2104`
   - API ID: `9cd8eb60-3222-4efc-bd7c-50e03e6a81a4`
   - Issue: "Manukau City" may need to be just "Manukau"

4. **PAK'nSAVE Mt Albert**
   - Address: `1167-1177 New North Road, Auckland, 1025`
   - API ID: `b2e98a14-c8ca-401e-99ed-edf74570c6f6`
   - Issue: Address range format (1167-1177)

5. **PAK'nSAVE Richmond**
   - Address: `Croucher and Talbot Streeet, Richmond, Nelson, 7020`
   - API ID: `5cf0392f-c187-4fc4-a463-eb269d2e8f45`
   - Issue: Corner address format, typo "Streeet"

6. **PAK'nSAVE Rotorua**
   - Address: `Cnr Fenton and Amohau Streets, Rotorua, 3010`
   - API ID: `7d48a781-4f68-4c91-a908-8659e1b22f95`
   - Issue: Corner address format with "Cnr"

7. **PAK'nSAVE Warkworth**
   - Address: `12 Hudson Road, Warkworth, 0910`
   - API ID: `8f0d70be-5cb7-464b-99cb-8b0130671895`
   - Issue: Unknown

## Liquor Centre (7 stores)

Geocoding attempted: 2026-01-01
Success rate: 40.0% (36/90)

### Failed Stores

1. **Liquor Centre Methven**
   - Address: `137 Main Street, Christchurch 7730`
   - Issue: Methven is not in Christchurch

2. **Liquor Centre Greenhithe**
   - Address: `Shop 3, 10 Greenhithe Road, Auckland 0632`
   - Issue: Shop prefix

3. **Liquor Centre Constellation**
   - Address: `Unit 8, 20 Constellation Drive, Mairangi Bay, North Shore City, Auckland 0632`
   - Issue: Unit prefix

4. **Liquor Centre St Lukes**
   - Address: `Unit 6, 55 Sainsbury Road, Auckland 1346`
   - Issue: Unit prefix

5. **Liquor Centre Browns Bay**
   - Address: `Shop 6, 94 Clyde Road, Auckland 0630`
   - Issue: Shop prefix

6. **Liquor Centre Meadowlands**
   - Address: `1A/125 Meadowlands Drive, Auckland 2014`
   - Issue: Unit format

7. **Liquor Centre Avenue Tauranga**
   - Address: `97 Eleventh Avenue, Tauranga, Tauranga Region 3110`
   - Issue: "Tauranga Region" instead of region name

Note: 47 additional Liquor Centre stores skipped due to fallback address

## Bottle O (46 stores)

Geocoding attempted: 2026-01-01
Success rate: 69.7% (106/152)
Failed count: 46 stores

Details not yet documented - to be added

---

## New World (144 stores)

**Status:** Cannot geocode - insufficient address data
**Issue:** All 144 stores only have city/suburb names as addresses (e.g., "Wellington", "Tauranga"), not street addresses
**Root cause:**
- New World website protected by Cloudflare anti-bot challenge
- No accessible public API for store locations
- Existing data file (`newworld_stores.json`) only contains city names

**Example records:**
```json
{
  "id": "f145f120-ba19-4524-9fc5-e8caf516e209",
  "name": "New World Kawerau",
  "region": "NI",
  "address": "Kawerau"
}
```

**Options:**
1. Manual data entry for all 144 stores
2. Wait for Cloudflare bypass solution
3. Find alternative API/data source

## Next Steps

1. Review failed addresses and attempt manual geocoding
2. Consider address normalization (removing "Shop", "Unit", "Cnr" prefixes)
3. Fix obvious typos (e.g., "Streeet" -> "Street")
4. Verify corner addresses manually
5. Update addresses with corrections and re-run geocoding
6. Find solution for New World store addresses (144 stores pending)
