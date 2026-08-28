# Apartment Review Models - Usage Guide

## Overview

The database schema consists of three main models:

- **User**: Represents users who write reviews
- **Apartment**: Represents physical apartments with OSM data
- **Review**: Represents user reviews of apartments

## Database Schema

### Apartment Model

The `Apartment` model stores comprehensive address and location data from OpenStreetMap:

**Key Features:**

- Unique constraint on normalized address (street, house_number, city, postcode, country_code)
- Stores OSM reference data (osm_type, osm_id, osm_class) for linking back to the map
- High-precision coordinates using DECIMAL type
- Indexed for efficient location-based queries

**Fields:**

- `uid`: UUID primary key
- `osm_type`, `osm_id`, `osm_class`: OpenStreetMap reference
- `street`, `house_number`, `city`, `state`, `postcode`, `country`, `country_code`: Normalized address
- `display_name`: Full formatted address from OSM
- `latitude`, `longitude`: Precise coordinates (DECIMAL)
- `created_at`, `updated_at`: Timestamps

### Review Model

The `Review` model stores detailed apartment reviews:

**Key Features:**

- Unique constraint: one review per user per apartment
- 5 category ratings (all optional)
- Indexed for efficient queries by apartment and user

**Fields:**

- `uid`: UUID primary key
- `apartment_uid`: Foreign key to Apartment
- `user_uid`: Foreign key to User
- `title`, `content`: Review text
- `landlord_rating`, `location_rating`, `condition_rating`, `value_rating`, `quietness_rating`: Category ratings (1-10, optional)
- `created_at`, `updated_at`: Timestamps

## Usage Examples

### 1. Creating an Apartment from OSM Data

```python
from schemas import OSMAddressData
from utils import get_or_create_apartment

# Data from Nominatim API
osm_data = OSMAddressData(
    osm_type="way",
    osm_id=123456789,
    class="building",
    road="Main Street",
    house_number="123",
    city="New York",
    state="New York",
    postcode="10001",
    country="United States",
    country_code="US",
    display_name="123 Main Street, New York, NY 10001, United States",
    lat="40.7589",
    lon="-73.9851"
)

# Get or create apartment (handles duplicates automatically)
apartment, created = get_or_create_apartment(db, osm_data)

if created:
    print(f"Created new apartment: {apartment.uid}")
else:
    print(f"Found existing apartment: {apartment.uid}")
```

### 2. Creating a Review

```python
from models import Review
from utils import get_user_review_for_apartment

# Check if user already reviewed this apartment
existing = get_user_review_for_apartment(db, apartment_uid, user_uid)
if existing:
    raise HTTPException(status_code=409, detail="Already reviewed")

# Create review
review = Review(
    apartment_uid=apartment_uid,
    user_uid=user_uid,
    title="Great apartment, minor issues",
    content="The apartment is spacious and well-maintained...",
    landlord_rating=5,
    location_rating=4,
    condition_rating=4,
    value_rating=3,
    quietness_rating=4
)

db.add(review)
db.commit()
```

### 3. Querying Apartments by Location

```python
from utils import get_apartments_by_location

# Find apartments within 1km of a location
apartments = get_apartments_by_location(
    db,
    latitude=40.7589,
    longitude=-73.9851,
    radius_km=1.0,
    limit=50
)
```

### 4. Getting Reviews for an Apartment

```python
from utils import get_reviews_for_apartment, calculate_apartment_average_rating

# Get all reviews
reviews = get_reviews_for_apartment(db, apartment_uid, limit=100)

# Calculate average rating
avg_rating = calculate_apartment_average_rating(db, apartment_uid)
print(f"Average rating: {avg_rating:.2f}")
```

## API Integration

See `example_endpoints.py` for complete FastAPI endpoint examples.

### Typical Workflow

1. **User searches for address** → Frontend calls Nominatim API
2. **User selects address** → Frontend sends OSM data to `/apartments/from-osm`
3. **Backend creates/finds apartment** → Returns apartment UID
4. **User writes review** → Frontend sends review to `/reviews` with apartment UID
5. **Backend validates** → Checks for duplicates, creates review

## Important Notes

### Why Create Apartment Records?

- **Stability**: OSM IDs can change; our UUIDs are permanent
- **Data Integrity**: Proper foreign key relationships
- **Performance**: Indexed queries, no duplicate reviews
- **Flexibility**: Can add apartment-specific data (photos, amenities, etc.)

### Address Deduplication

The unique constraint on `(street, house_number, city, postcode, country_code)` prevents duplicate apartments. The `get_or_create_apartment()` function handles this automatically.

### OSM Data Mapping

OSM/Nominatim returns various field names for the same data:

- City: `city`, `town`, or `village`
- Street: `road`
- Class: `class` (aliased in schema)

The `OSMAddressData` schema handles these variations.

## Database Migrations

To apply the schema changes, restart your FastAPI app. SQLModel will create the tables automatically via `SQLModel.metadata.create_all(engine)` in `main.py`.

For production, consider using Alembic for proper migrations.
