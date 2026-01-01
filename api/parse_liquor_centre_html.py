"""Parse Liquor Centre stores from scraped HTML."""
import re
import json
from bs4 import BeautifulSoup


def main():
    """Parse stores from HTML."""
    print("Parsing Liquor Centre stores from HTML...")

    with open("/Users/axelmckenna/Liquorfy/api/data/liquor_centre_raw.html", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    stores = []

    # Find all store cards
    store_cards = soup.find_all('div', class_='StoreCard')
    print(f"Found {len(store_cards)} store cards")

    for card in store_cards:
        # Get store name
        name_elem = card.find('span', class_='StoreCard__Name')
        if not name_elem:
            continue

        name = name_elem.get_text(strip=True)

        # Get store details (hours, address, etc.)
        details_elem = card.find('span', class_='StoreCard__Details')
        details_text = details_elem.get_text(separator='\n', strip=True) if details_elem else ""

        # Parse details
        lines = [line.strip() for line in details_text.split('\n') if line.strip()]

        hours = None
        address_parts = []
        phone = None

        for line in lines:
            # Check if it's opening hours
            if re.search(r'open|closed|\d{1,2}:\d{2}\s*(?:am|pm)', line.lower()):
                hours = line
            # Check if it's a phone number
            elif re.search(r'\(?\d{2,4}\)?[-\s]?\d{3,4}[-\s]?\d{3,4}', line):
                phone = line
            # Otherwise it's probably part of the address
            else:
                address_parts.append(line)

        address = ', '.join(address_parts) if address_parts else None

        # Find the catalogue link to get the slug
        slug = None
        catalogue_link = card.find_parent('div').find('a', href=re.compile(r'\.shop\.liquor-centre\.co\.nz/catalogues')) if card.find_parent('div') else None
        if not catalogue_link:
            # Try finding it in nearby elements
            parent = card.find_parent()
            if parent:
                catalogue_link = parent.find('a', href=re.compile(r'\.shop\.liquor-centre\.co\.nz/catalogues'))

        if catalogue_link:
            href = catalogue_link.get('href', '')
            match = re.search(r'https?://([^.]+)\.shop\.liquor-centre\.co\.nz', href)
            if match:
                slug = match.group(1)

        # If we couldn't find the slug, try to derive it from the name
        if not slug and name:
            # Convert name to slug format
            slug = name.lower().replace(' ', '-').replace('liquor-centre-', '').replace('liquor-centre', '')
            slug = re.sub(r'[^a-z0-9-]', '', slug)

        stores.append({
            'slug': slug,
            'name': name,
            'address': address,
            'hours': hours,
            'phone': phone
        })

    print(f"\nExtracted {len(stores)} stores")

    # Print first 10 stores
    print("\nFirst 10 stores:")
    for i, store in enumerate(stores[:10]):
        print(f"\n{i+1}. {store['slug']}")
        print(f"   Name: {store.get('name')}")
        print(f"   Address: {store.get('address')}")
        print(f"   Hours: {store.get('hours')}")

    # Save to JSON
    output_file = "/Users/axelmckenna/Liquorfy/api/data/liquor_centre_stores_parsed.json"
    with open(output_file, "w") as f:
        json.dump(stores, f, indent=2)

    print(f"\n✓ Stores saved to {output_file}")

    # Also save just the slugs for comparison
    slugs = [s['slug'] for s in stores if s.get('slug')]
    slugs_file = "/Users/axelmckenna/Liquorfy/api/data/liquor_centre_slugs_new.json"
    with open(slugs_file, "w") as f:
        json.dump(sorted(set(slugs)), f, indent=2)

    print(f"✓ {len(set(slugs))} unique slugs saved to {slugs_file}")


if __name__ == "__main__":
    main()
