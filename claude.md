# CLAUDE.md - Styling Agent POC

## Project Overview

A web application POC that demonstrates an AI-powered styling agent for online clothing companies. The agent takes a photo of a user and a clothing item, virtually tries the item on the user, and recommends complementary items to increase revenue through outfit completion.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           STYLING AGENT POC                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────────┐    ┌─────────────────────┐   │
│  │   Frontend   │───▶│  Backend API     │───▶│  Model Services     │   │
│  │   (React)    │◀───│  (FastAPI)       │◀───│                     │   │
│  └──────────────┘    └──────────────────┘    │  ┌───────────────┐  │   │
│         │                    │               │  │ Virtual Try-On │  │   │
│         │                    │               │  │ (IDM-VTON/     │  │   │
│         ▼                    ▼               │  │  Kolors-VTON)  │  │   │
│  ┌──────────────┐    ┌──────────────────┐   │  └───────────────┘  │   │
│  │ User Uploads │    │ Session Manager  │   │                     │   │
│  │ - Person img │    │ - State tracking │   │  ┌───────────────┐  │   │
│  │ - Garment img│    │ - Try-on history │   │  │ FashionCLIP   │  │   │
│  └──────────────┘    └──────────────────┘   │  │ (Embeddings)  │  │   │
│                                              │  └───────────────┘  │   │
│                                              │                     │   │
│                      ┌──────────────────┐   │  ┌───────────────┐  │   │
│                      │ Product Catalog  │   │  │ Outfit Recomm │  │   │
│                      │ (Vector DB)      │◀──│──│ Engine        │  │   │
│                      │ - Embeddings     │   │  └───────────────┘  │   │
│                      │ - Metadata       │   │                     │   │
│                      └──────────────────┘   └─────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## User Flow

1. **Upload Phase**: User uploads their photo + selects a clothing item
2. **Try-On Phase**: System generates virtual try-on image showing user wearing the item
3. **Recommendation Phase**: Below the try-on image, system displays complementary items (pants, shoes, accessories)
4. **Interactive Loop**: User clicks a recommended item → new try-on generated with both items → new recommendations shown

---

## Key Models & Tools

### 1. Virtual Try-On Model

**Primary Choice: Nano Banana Pro (Google DeepMind)**
- Source: [Replicate](https://replicate.com/google/nano-banana-pro)
- Runs: 9.4M+
- Pricing: $0.15/image (2K resolution)
- Why: Production-ready API, commercially viable, high quality output, no licensing restrictions
- Integration: Simple REST API via Replicate - no GPU infrastructure needed

**Fallback Options (for reference only):**
- IDM-VTON: [GitHub](https://github.com/yisol/IDM-VTON) - CC BY-NC-SA 4.0 (non-commercial only)
- Kolors VTON: [HuggingFace](https://huggingface.co/spaces/Kwai-Kolors/Kolors-Virtual-Try-On) - demo only

### 2. Outfit Recommendation Engine

**Primary: FashionCLIP**
- Source: [HuggingFace](https://huggingface.co/patrickjohncyh/fashion-clip)
- Downloads: 2.2M+ monthly
- What it does: Creates embeddings for fashion items that understand style, category, and visual features
- Use case: Embed your product catalog, then find complementary items based on style similarity

**How to Use FashionCLIP for Recommendations:**
```python
from transformers import CLIPProcessor, CLIPModel

model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip")
processor = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")

# Embed all catalog items
# For a given item, find items that:
# 1. Are in complementary categories (top → bottom, dress → shoes)
# 2. Have similar style embeddings
# 3. Match color palettes
```

### 3. Replicate Integration

**Using Nano Banana Pro via Replicate API:**
```python
import replicate

output = replicate.run(
    "google/nano-banana-pro",
    input={
        "person_image": person_image_url,
        "garment_image": garment_image_url,
        # Additional parameters as needed
    }
)
```
- Async support for handling 30-60s generation times
- Webhook callbacks available for job completion

---

## Tech Stack Recommendation

### Frontend
- React with TypeScript
- TailwindCSS for styling
- React Query for API state management
- Image upload with drag-and-drop (react-dropzone)

### Backend
- FastAPI (Python) - matches ML ecosystem
- Celery + Redis for async job processing (try-on takes 30-60s)
- PostgreSQL for user sessions
- Pinecone/Qdrant for vector similarity search (product embeddings)

### ML Infrastructure
- Replicate API for Nano Banana Pro (virtual try-on)
- FashionCLIP can run on CPU for embeddings (or use HuggingFace Inference API)
- No local GPU required - fully cloud-based inference

---

## Data Requirements

### Product Catalog

You'll need for each item:
- High-quality product image (transparent/white background preferred)
- Category (top, bottom, dress, shoes, accessory)
- Subcategory (t-shirt, jeans, sneakers, etc.)
- Style tags (casual, formal, sporty, etc.)
- Color information
- FashionCLIP embedding (pre-computed)

### Sample Datasets for POC
- **DressCode**: [GitHub](https://github.com/aimagelab/dress-code) - Multi-category try-on dataset
- **VITON-HD**: High-resolution try-on pairs
- **DeepFashion**: General fashion dataset

---

## API Design

```yaml
POST /api/v1/try-on
  Input:
    - person_image: file
    - garment_image: file
    - garment_category: string (upper_body, lower_body, full_body)
  Output:
    - job_id: string

GET /api/v1/try-on/{job_id}
  Output:
    - status: pending | processing | completed | failed
    - result_image_url: string (when completed)

POST /api/v1/recommendations
  Input:
    - current_garments: list[garment_id]
    - person_style_embedding: optional
    - num_recommendations: int
  Output:
    - recommendations: list[{garment_id, category, image_url, match_score}]

POST /api/v1/composite-try-on
  Input:
    - person_image: file
    - garment_ids: list[garment_id]  # Multiple items to try on
  Output:
    - job_id: string
```

---

## Recommendation Logic

```python
def get_outfit_recommendations(current_item, catalog_embeddings, k=6):
    """
    Given a selected item, recommend complementary pieces.
    """
    # 1. Determine complementary categories
    category_map = {
        'top': ['bottom', 'shoes', 'accessory'],
        'bottom': ['top', 'shoes', 'accessory'],
        'dress': ['shoes', 'accessory', 'outerwear'],
        'shoes': ['top', 'bottom', 'accessory'],
    }
    target_categories = category_map[current_item.category]

    # 2. Filter catalog to complementary categories
    candidates = catalog.filter(category__in=target_categories)

    # 3. Use FashionCLIP to find style-compatible items
    current_embedding = get_embedding(current_item.image)

    # 4. Score by style similarity + category diversity
    scored = []
    for item in candidates:
        style_score = cosine_similarity(current_embedding, item.embedding)
        # Boost items from underrepresented categories
        scored.append((item, style_score))

    # 5. Return top-k, ensuring category diversity
    return select_diverse_top_k(scored, k)
```

---

## Directory Structure

```
styling-agent-poc/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ImageUploader.tsx
│   │   │   ├── TryOnViewer.tsx
│   │   │   ├── RecommendationGrid.tsx
│   │   │   └── OutfitBuilder.tsx
│   │   ├── hooks/
│   │   │   └── useTryOn.ts
│   │   └── App.tsx
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── tryon.py
│   │   │   └── recommendations.py
│   │   ├── services/
│   │   │   ├── tryon_service.py
│   │   │   ├── embedding_service.py
│   │   │   └── recommendation_engine.py
│   │   └── models/
│   │       └── schemas.py
│   ├── workers/
│   │   └── tryon_worker.py
│   └── requirements.txt
├── ml/
│   ├── idm_vton/           # IDM-VTON model code
│   ├── fashion_clip/       # FashionCLIP embeddings
│   └── scripts/
│       └── embed_catalog.py
├── data/
│   ├── catalog/            # Product images
│   └── embeddings/         # Pre-computed embeddings
├── docker-compose.yml
└── CLAUDE.md
```

---

## Quick Start Commands

```bash
# 1. Install Python dependencies
pip install replicate transformers torch fastapi uvicorn

# 2. Set up Replicate API key
export REPLICATE_API_TOKEN=your_token_here

# 3. Start backend
cd backend
uvicorn app.main:app --reload

# 4. Start frontend
cd frontend
npm install && npm run dev
```

---

## POC Demo Script

1. **Demo Opening**: "Here's how AI can increase average order value for your clothing store"
2. **Upload**: Show user uploading their photo
3. **Select Item**: User picks a shirt from catalog
4. **Try-On**: Watch the AI generate the try-on image (30-60s)
5. **Recommendations**: "Based on this shirt, here are matching items..."
6. **Add to Cart**: User clicks jeans → see try-on with both items
7. **Revenue Impact**: "Users who use virtual try-on add 2.3 more items on average"

---

## Key Resources

| Resource | URL |
|----------|-----|
| Nano Banana Pro | https://replicate.com/google/nano-banana-pro |
| Replicate Docs | https://replicate.com/docs |
| FashionCLIP | https://huggingface.co/patrickjohncyh/fashion-clip |
| DressCode Dataset | https://github.com/aimagelab/dress-code |
| Awesome VTON List | https://github.com/minar09/awesome-virtual-try-on |

---

## Next Steps

- [ ] Set up Replicate API key and test Nano Banana Pro
- [ ] Embed sample catalog with FashionCLIP
- [ ] Build FastAPI backend with try-on endpoint (Replicate integration)
- [ ] Create React frontend with upload flow
- [ ] Implement recommendation engine
- [ ] Add multi-item try-on support
- [ ] Polish UI for demo presentation
