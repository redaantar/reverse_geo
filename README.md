# Reverse Geocoding Processor

A Python utility for reverse geocoding coordinates (latitude and longitude) to human-readable addresses using Google Maps API.

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Required Packages

Install the required packages using pip:

```bash
pip install pandas geopy googlemaps

```

```bash
python3 geo_processor.py --input coordinates.csv --output addresses.csv --api-key [GMAPS API KEY]
```