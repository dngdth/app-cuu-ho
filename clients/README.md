# Rescue API Clients

This directory contains modular Python clients for interacting with the Rescue API.

## Structure

- `base_client.py` - Base API client with common HTTP methods
- `rescue_request_client.py` - Client for rescue request operations
- `needs_client.py` - Client for needs operations
- `disaster_type_client.py` - Client for disaster type operations
- `region_client.py` - Client for region operations
- `geocode_client.py` - Client for geocoding operations
- `health_client.py` - Client for health check operations
- `rescue_api_client.py` - Main client that combines all resource clients

## Usage

### Using Individual Clients

```python
from clients.rescue_request_client import RescueRequestClient
from clients.needs_client import NeedsClient

# Initialize clients
rescue_client = RescueRequestClient()
needs_client = NeedsClient()

# Get all rescue requests
requests = rescue_client.get_all(limit=10)

# Create a new need
new_need = needs_client.create({"name": "Food", "description": "Emergency food supplies"})
```

### Using the Main Client

```python
from clients import RescueAPIClient

# Initialize main client
client = RescueAPIClient()

# All clients are available as attributes
requests = client.rescue_requests.get_all()
needs = client.needs.get_all()
regions = client.regions.get_all()
coords = client.geocode.forward_geocode("Quận 1, Hồ Chí Minh")
```

## API Endpoints Covered

### Rescue Requests (`/rescue_request/`)
- `get_all(**params)` - Get all with filtering/pagination
- `get_by_id(id)` - Get by ID
- `create(data)` - Create new
- `update(id, data)` - Update existing
- `delete(id)` - Delete

### Needs (`/needs/`)
- `get_all()` - Get all needs
- `get_by_id(id)` - Get by ID
- `create(data)` - Create new
- `update(id, data)` - Update existing
- `delete(id)` - Delete

### Disaster Types (`/disaster-type/`)
- `get_all()` - Get all disaster types
- `get_by_id(id)` - Get by ID
- `create(data)` - Create new
- `update(id, data)` - Update existing
- `delete(id)` - Delete

### Regions (`/region/`)
- `get_all()` - Get all regions
- `get_by_id(id)` - Get by ID
- `create(data)` - Create new
- `update(id, data)` - Update existing
- `delete(id)` - Delete
- `import_csv(file_path)` - Import from CSV

### Geocoding (`/geocode/`)
- `forward_geocode(address)` - Convert address to coordinates

### Health Check (`/health`)
- `check()` - API health check

## Error Handling

All methods will raise `requests.HTTPError` for HTTP errors (4xx, 5xx). Handle exceptions appropriately:

```python
try:
    requests = client.rescue_requests.get_all()
except requests.HTTPError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Other error: {e}")
```

## Configuration

By default, clients connect to `http://localhost:8099`. To use a different URL:

```python
client = RescueAPIClient("https://your-api-domain.com")
# or
rescue_client = RescueRequestClient("https://your-api-domain.com")
```
