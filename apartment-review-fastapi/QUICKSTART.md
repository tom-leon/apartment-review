# Quick Start Guide

## What Was Created

### 1. Enhanced Models (`models.py`)

- **User**: Added `created_at` and `updated_at` timestamps
- **Apartment**: Complete OSM integration with:
  - OSM reference data (osm_type, osm_id, osm_class)
  - Normalized address components (street, house_number, city, state, postcode, country, country_code)
  - High-precision coordinates (DECIMAL type)
  - Unique constraint on address to prevent duplicates
  - Location index for efficient queries
- **Review**: Enhanced with:
  - Title and content fields
  - 5 category ratings (landlord, location, condition, value, quietness)
  - Unique constraint: one review per user per apartment
  - Proper indexes

### 2. Pydantic Schemas (`schemas.py`)

- `OSMAddressData`: For parsing Nominatim API responses
- `ApartmentCreate` & `ApartmentResponse`: For apartment operations
- `ReviewCreate` & `ReviewResponse`: For review operations
- `UserResponse`: For user data (without password)

### 3. Utility Functions (`utils.py`)

- `get_or_create_apartment()`: Smart apartment creation with duplicate handling
- `get_apartment_by_id()`: Fetch apartment by UUID
- `get_apartments_by_location()`: Find nearby apartments
- `get_reviews_for_apartment()`: Get all reviews for an apartment
- `get_user_review_for_apartment()`: Check if user already reviewed
- `calculate_apartment_average_rating()`: Calculate average rating

### 4. Example Endpoints (`example_endpoints.py`)

Complete FastAPI endpoint examples showing:

- Creating apartments from OSM data
- Creating reviews with validation
- Querying apartments and reviews
- Proper error handling

## How to Use

### Step 1: Update Database Schema

The models will auto-create tables when you restart your FastAPI app:

```bash
# Make sure your database is running
# Then restart the API
python main.py
```

SQLModel will automatically create the new tables and columns via `SQLModel.metadata.create_all(engine)`.

### Step 2: Test the Models

Here's a complete example workflow:

```python
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import OSMAddressData
from utils import get_or_create_apartment
from models import Review

# Create a database session
db = SessionLocal()

# 1. Create apartment from OSM data (from Nominatim API)
osm_data = OSMAddressData(
    osm_type="way",
    osm_id=123456789,
    class_="building",
    road="123 Main St",
    house_number="123",
    city="New York",
    postcode="10001",
    country="United States",
    country_code="US",
    display_name="123 Main St, New York, NY 10001, USA",
    lat="40.7589",
    lon="-73.9851"
)

apartment, created = get_or_create_apartment(db, osm_data)
print(f"Apartment UID: {apartment.uid}")

# 2. Create a review
review = Review(
    apartment_uid=apartment.uid,
    user_uid=user.uid,  # Your user UID
    title="Great location!",
    content="Nice apartment in a great neighborhood",
    landlord_rating=9,
    location_rating=10,
    condition_rating=8,
    value_rating=7,
    quietness_rating=8
)

db.add(review)
db.commit()
print(f"Review created: {review.uid}")

db.close()
```

### Step 3: Integrate with Your API

You can either:

**Option A: Copy endpoints to main.py**

```python
# In main.py, add the endpoints from example_endpoints.py
```

**Option B: Use as a router**

```python
# In main.py
from example_endpoints import router as apartment_router

app.include_router(apartment_router, prefix="/api/v1", tags=["apartments"])
```

## Frontend Integration

### 1. User Searches for Address

```typescript
// Frontend calls Nominatim
const response = await fetch(
  `https://nominatim.openstreetmap.org/search?` +
    `q=${encodeURIComponent(searchQuery)}&format=json&addressdetails=1`
);
const results = await response.json();
```

### 2. User Selects Address & Creates Review

```typescript
// Send OSM data to your backend
const apartment = await fetch("/api/v1/apartments/from-osm", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(results[0]), // OSM data
});

const apartmentData = await apartment.json();

// Create review
const review = await fetch("/api/v1/reviews", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  },
  body: JSON.stringify({
    apartment_uid: apartmentData.uid,
    rating: 8,
    title: "Great place!",
    content: "...",
    landlord_rating: 9,
    location_rating: 8,
    // ... other ratings
  }),
});
```

## Key Benefits

✅ **No Duplicate Apartments**: Unique constraint on normalized address  
✅ **No Duplicate Reviews**: One review per user per apartment  
✅ **OSM Integration**: Stores OSM IDs for map linking  
✅ **Stable IDs**: Your own UUIDs won't change even if OSM data changes  
✅ **Rich Data**: Multiple rating categories for detailed reviews  
✅ **Efficient Queries**: Proper indexes on location and relationships

## Next Steps

1. Test the models with your database
2. Integrate the endpoints into your API
3. Update your frontend to use the new apartment creation flow
4. Consider adding:
   - Apartment photos
   - User authentication
   - Review moderation
   - Average rating calculation endpoint
   - Search/filter endpoints

See `MODELS_USAGE.md` for detailed documentation.
