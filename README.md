# Stylist AI - Virtual Try-On

Virtual try-on + style recommendations powered by FastFit and FashionCLIP.

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Scrape Product Catalog

```bash
# Test scrape (10 items)
python scripts/scrape.py --test -s terminalx

# Full scrape from TerminalX (product-only images)
python scripts/scrape.py -s terminalx

# Scrape from Raven.co.il
python scripts/scrape.py -s raven

# Scrape all sources
python scripts/scrape.py

# Limit items
python scripts/scrape.py -s terminalx --limit 100
```

Output: `data/catalog/{source}.json`

**Available scrapers:**
- `matimli` - Matimli.co.il (WooCommerce store)
- `terminalx` - TerminalX.com (product-only images, no models)
- `raven` - Raven.co.il (Shopify store)

### 3. Start Qdrant (Vector Database)

```bash
docker run -d -p 6333:6333 -p 6334:6334 \
  -v qdrant_data:/qdrant/storage \
  qdrant/qdrant
```

### 4. Generate Embeddings

```bash
# Test embeddings (no Qdrant required)
python scripts/embed.py --test

# Full embedding generation (requires Qdrant running)
python scripts/embed.py --recreate
```

### 5. Start API Server

```bash
uvicorn api.main:app --reload
```

API available at: http://localhost:8000

### 6. Start Frontend (coming soon)

```bash
cd webapp && npm install && npm run dev
```

---

## Project Structure

```
VTO/
├── api/                    # FastAPI backend
│   ├── main.py            # App entry point
│   ├── routes/
│   │   ├── tryon.py       # Virtual try-on endpoints
│   │   └── recommend.py   # Recommendation endpoints
│   └── services/
│       ├── fastfit.py     # FastFit model service
│       ├── embeddings.py  # FashionCLIP embeddings
│       └── vector_store.py # Qdrant vector store
├── scrapers/              # Product catalog scrapers
│   ├── base.py           # Base scraper class
│   ├── raven.py          # Raven.co.il scraper (Shopify)
│   ├── terminalx.py      # TerminalX scraper (product-only images)
│   └── registry.py       # Scraper registry
├── scripts/              # Utility scripts
│   ├── scrape.py         # Run catalog scraping
│   └── embed.py          # Generate embeddings
├── data/
│   └── catalog/          # Scraped product data
├── webapp/               # React frontend (coming soon)
├── requirements.txt
├── docker-compose.yml
└── Dockerfile
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/api/tryon/single` | POST | Try on single garment |
| `/api/tryon/multi` | POST | Try on multiple garments |
| `/api/recommend/complementary` | POST | Get complementary items |
| `/api/recommend/catalog` | GET | Browse catalog |

### Example: Try-On Single Garment

```bash
curl -X POST "http://localhost:8000/api/tryon/single" \
  -F "person=@photo.jpg" \
  -F "garment_url=https://raven.co.il/cdn/shop/files/image.jpg" \
  -F "category=upper_body"
```

### Example: Get Recommendations

```bash
curl -X POST "http://localhost:8000/api/recommend/complementary" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "9471652626707",
    "categories": ["lower_body", "shoes"],
    "exclude_ids": []
  }'
```

---

## Scripts Reference

### scrape.py

```bash
# Scrape specific source
python scripts/scrape.py -s terminalx

# Scrape all sources
python scripts/scrape.py

# Test mode (10 items only)
python scripts/scrape.py --test -s terminalx

# Limit number of items
python scripts/scrape.py -s terminalx --limit 50

# Custom output directory
python scripts/scrape.py -o /path/to/output
```

### embed.py

```bash
# Test mode (no Qdrant required)
python scripts/embed.py --test

# Generate embeddings for all catalog items
python scripts/embed.py

# Recreate collection (delete existing)
python scripts/embed.py --recreate

# Specific source only
python scripts/embed.py -s raven
```

---

## Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- API: http://localhost:8000
- Webapp: http://localhost:3000
- Qdrant: http://localhost:6333

---

## Adding New Scrapers

1. Create `scrapers/{site}.py` inheriting from `BaseScraper`
2. Implement `scrape_all()` and `map_category()`
3. Add to `scrapers/registry.py`
4. Run scrape and embed scripts

Example:

```python
# scrapers/newsite.py
from .base import BaseScraper, Item

class NewSiteScraper(BaseScraper):
    SOURCE = "newsite"
    BASE_URL = "https://newsite.com"

    def scrape_all(self) -> list[Item]:
        # Implement scraping logic
        pass

    def map_category(self, raw: str) -> str:
        # Map raw category to: upper_body, lower_body, shoes, bags, etc.
        pass
```

---

## Troubleshooting

### Qdrant Connection Error

```
Error: [Errno 61] Connection refused
```

Make sure Qdrant is running:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### FashionCLIP NaN Values

If embeddings return NaN values, try:
```bash
pip install --upgrade fashion-clip torch
```

### Scraping Blocked

Some sites may block automated requests. Try:
- Adding delays between requests
- Using a proxy
- Checking if the site has an API

---

## Requirements

- Python 3.10+
- Docker (for Qdrant)
- ~5GB disk space (for FastFit model)
- GPU recommended (CUDA or Apple MPS)

---

## License

MIT
