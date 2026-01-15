# Stylist AI Agent

Virtual try-on + style recommendations powered by FastFit and FashionCLIP.

## Quick Start

```bash
# Setup
conda create -n stylist python=3.10 && conda activate stylist
pip install -r requirements.txt

# Run
python scripts/scrape.py          # Scrape Reaven catalog
python scripts/embed.py           # Generate embeddings
uvicorn api.main:app --reload     # Start backend
cd webapp && npm run dev          # Start frontend
```

---

## Architecture

```
User Photo + Item Selection
        │
        ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   FastFit    │     │ FashionCLIP  │     │   Qdrant     │
│   (Try-On)   │     │ (Embeddings) │     │ (Vector DB)  │
└──────────────┘     └──────────────┘     └──────────────┘
        │                   │                    │
        └───────────────────┴────────────────────┘
                            │
                            ▼
                    Web App (React)
```

---

## Project Structure

```
stylist-ai/
├── claude.md
├── requirements.txt
├── docker-compose.yml
│
├── api/
│   ├── main.py
│   ├── routes/
│   │   ├── tryon.py
│   │   └── recommend.py
│   └── services/
│       ├── fastfit.py
│       ├── embeddings.py
│       └── vector_store.py
│
├── scrapers/
│   ├── base.py
│   ├── reaven.py
│   └── registry.py
│
├── webapp/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── hooks/
│   │   └── store.ts
│   └── package.json
│
├── scripts/
│   ├── scrape.py
│   └── embed.py
│
└── data/
    ├── catalog/
    └── models/
```

---

## Core Services

### FastFit Service

```python
# api/services/fastfit.py
import torch
from diffusers import StableDiffusionInpaintPipeline

class FastFitService:
    def __init__(self):
        self.pipe = None
    
    def load(self):
        self.pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "zhengchong/FastFit-MR-1024",
            torch_dtype=torch.float16
        ).to("cuda")
    
    def try_on(self, person_img, garment_img, category):
        result = self.pipe(
            image=person_img,
            garment=garment_img,
            category=category,
            num_inference_steps=30,
            guidance_scale=2.5
        )
        return result.images[0]
```

### Embedding Service

```python
# api/services/embeddings.py
from fashion_clip.fashion_clip import FashionCLIP
import numpy as np
from PIL import Image

class EmbeddingService:
    def __init__(self, model_name: str = "fashion-clip"):
        self.fclip = FashionCLIP(model_name)

    def embed_image(self, image: Image.Image) -> np.ndarray:
        """Generate normalized embedding for a single image."""
        embedding = self.fclip.encode_images([image], batch_size=1)[0]
        return embedding / np.linalg.norm(embedding, ord=2)

    def embed_images(self, images: list[Image.Image], batch_size: int = 32) -> np.ndarray:
        """Generate normalized embeddings for multiple images."""
        embeddings = self.fclip.encode_images(images, batch_size=batch_size)
        return embeddings / np.linalg.norm(embeddings, ord=2, axis=-1, keepdims=True)

    def embed_text(self, text: str) -> np.ndarray:
        """Generate normalized embedding for a single text."""
        embedding = self.fclip.encode_text([text], batch_size=1)[0]
        return embedding / np.linalg.norm(embedding, ord=2)

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Generate normalized embeddings for multiple texts."""
        embeddings = self.fclip.encode_text(texts, batch_size=batch_size)
        return embeddings / np.linalg.norm(embeddings, ord=2, axis=-1, keepdims=True)
```

### Vector Store

```python
# api/services/vector_store.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class VectorStore:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)
        self.collection = "fashion_items"
    
    def create_collection(self):
        self.client.create_collection(
            self.collection,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE)
        )
    
    def upsert(self, item_id, vector, payload):
        self.client.upsert(self.collection, [
            PointStruct(id=item_id, vector=vector, payload=payload)
        ])
    
    def search(self, vector, categories, exclude_ids, limit=10):
        return self.client.search(
            self.collection,
            query_vector=vector,
            query_filter={
                "must": [{"key": "category", "match": {"any": categories}}],
                "must_not": [{"key": "item_id", "match": {"any": exclude_ids}}]
            },
            limit=limit
        )
```

---

## Scrapers

### Base Scraper

```python
# scrapers/base.py
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class Item:
    id: str
    source: str
    name: str
    price: float
    currency: str
    category: str
    image_url: str
    product_url: str

class BaseScraper(ABC):
    SOURCE: str = ""
    
    @abstractmethod
    def scrape_all(self) -> list[Item]:
        pass
    
    @abstractmethod
    def map_category(self, raw: str) -> str:
        pass
```

### Reaven Scraper (Shopify)

Reaven uses Shopify — products available at `/products.json`.

```python
# scrapers/reaven.py
import httpx
from .base import BaseScraper, Item

class ReavenScraper(BaseScraper):
    SOURCE = "reaven"
    BASE_URL = "https://www.reaven.co"
    
    CATEGORY_MAP = {
        "hoodie": "upper_body",
        "crewneck": "upper_body",
        "t-shirt": "upper_body",
        "jacket": "upper_body",
        "bomber": "upper_body",
        "flannel": "upper_body",
        "pants": "lower_body",
        "shorts": "lower_body",
    }
    
    def scrape_all(self) -> list[Item]:
        items = []
        page = 1
        
        while True:
            resp = httpx.get(f"{self.BASE_URL}/products.json?limit=250&page={page}")
            products = resp.json().get("products", [])
            
            if not products:
                break
            
            for p in products:
                items.append(self._parse(p))
            page += 1
        
        return items
    
    def _parse(self, p: dict) -> Item:
        return Item(
            id=str(p["id"]),
            source=self.SOURCE,
            name=p["title"],
            price=float(p["variants"][0]["price"]),
            currency="EUR",
            category=self.map_category(p.get("product_type", "")),
            image_url=p["images"][0]["src"] if p["images"] else "",
            product_url=f"{self.BASE_URL}/products/{p['handle']}"
        )
    
    def map_category(self, raw: str) -> str:
        for key, cat in self.CATEGORY_MAP.items():
            if key in raw.lower():
                return cat
        return "upper_body"
```

### Registry

```python
# scrapers/registry.py
from .reaven import ReavenScraper

SCRAPERS = {
    "reaven": ReavenScraper,
    # "asos": AsosScraper,
    # "zara": ZaraScraper,
}

def get_scraper(name: str):
    return SCRAPERS[name]()
```

---

## API

### Main App

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import tryon, recommend

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(tryon.router, prefix="/api/tryon")
app.include_router(recommend.router, prefix="/api/recommend")
```

### Try-On Route

```python
# api/routes/tryon.py
from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/single")
async def try_on_single(person: UploadFile, garment_url: str, category: str):
    # Process with FastFit
    return {"image_url": "result.jpg"}

@router.post("/multi")
async def try_on_multi(person: UploadFile, garments: list[dict]):
    # Process multiple items
    return {"image_url": "result.jpg"}
```

### Recommend Route

```python
# api/routes/recommend.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class RecommendRequest(BaseModel):
    item_id: str
    categories: list[str]
    exclude_ids: list[str] = []

@router.post("/complementary")
async def get_complementary(req: RecommendRequest):
    # Query vector store
    return {"items": []}
```

---

## Web App

### Store (Zustand)

```typescript
// webapp/src/store.ts
import { create } from 'zustand';

interface Item {
  id: string;
  name: string;
  price: number;
  category: string;
  imageUrl: string;
}

interface Store {
  personPhoto: string | null;
  selectedItems: Item[];
  shownIds: Set<string>;
  tryOnResult: string | null;
  
  setPhoto: (p: string) => void;
  addItem: (i: Item) => void;
  removeItem: (id: string) => void;
  setTryOnResult: (url: string) => void;
  markShown: (ids: string[]) => void;
  reset: () => void;
  getNextCategories: () => string[];
}

const FLOW: Record<string, string[]> = {
  upper_body: ['lower_body', 'shoes', 'bags'],
  lower_body: ['shoes', 'bags'],
  dresses: ['shoes', 'bags'],
  shoes: ['bags'],
  bags: [],
};

export const useStore = create<Store>((set, get) => ({
  personPhoto: null,
  selectedItems: [],
  shownIds: new Set(),
  tryOnResult: null,
  
  setPhoto: (p) => set({ personPhoto: p }),
  addItem: (i) => set((s) => ({
    selectedItems: [...s.selectedItems, i],
    shownIds: new Set([...s.shownIds, i.id]),
  })),
  removeItem: (id) => set((s) => ({
    selectedItems: s.selectedItems.filter((i) => i.id !== id),
  })),
  setTryOnResult: (url) => set({ tryOnResult: url }),
  markShown: (ids) => set((s) => ({
    shownIds: new Set([...s.shownIds, ...ids]),
  })),
  reset: () => set({
    personPhoto: null,
    selectedItems: [],
    shownIds: new Set(),
    tryOnResult: null,
  }),
  getNextCategories: () => {
    const cats = get().selectedItems.map((i) => i.category);
    if (cats.includes('dresses')) {
      return ['shoes', 'bags'].filter((c) => !cats.includes(c));
    }
    const last = cats[cats.length - 1] || 'upper_body';
    return (FLOW[last] || []).filter((c) => !cats.includes(c));
  },
}));
```

### App Component

```tsx
// webapp/src/App.tsx
import { PhotoUploader } from './components/PhotoUploader';
import { CatalogGrid } from './components/CatalogGrid';
import { TryOnResult } from './components/TryOnResult';
import { Recommendations } from './components/Recommendations';
import { useStore } from './store';

export default function App() {
  const { personPhoto, selectedItems } = useStore();
  
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <h1 className="text-2xl font-bold mb-6">Stylist AI</h1>
      
      {!personPhoto ? (
        <PhotoUploader />
      ) : selectedItems.length === 0 ? (
        <CatalogGrid />
      ) : (
        <>
          <TryOnResult />
          <Recommendations />
        </>
      )}
    </div>
  );
}
```

### Photo Uploader

```tsx
// webapp/src/components/PhotoUploader.tsx
import { useDropzone } from 'react-dropzone';
import { useStore } from '../store';

export function PhotoUploader() {
  const setPhoto = useStore((s) => s.setPhoto);
  
  const { getRootProps, getInputProps } = useDropzone({
    accept: { 'image/*': [] },
    onDrop: ([f]) => {
      const r = new FileReader();
      r.onload = () => setPhoto(r.result as string);
      r.readAsDataURL(f);
    },
  });
  
  return (
    <div {...getRootProps()} className="border-2 border-dashed p-12 text-center rounded-xl cursor-pointer">
      <input {...getInputProps()} />
      <p>📸 Upload your full body photo</p>
    </div>
  );
}
```

### Try-On Result

```tsx
// webapp/src/components/TryOnResult.tsx
import { useStore } from '../store';

export function TryOnResult() {
  const { personPhoto, tryOnResult, selectedItems, removeItem } = useStore();
  
  return (
    <div className="flex gap-6 mb-6">
      <img src={tryOnResult || personPhoto!} className="flex-1 rounded-xl max-w-md" />
      <div className="w-48">
        <h3 className="font-semibold mb-2">Selected</h3>
        {selectedItems.map((i) => (
          <div key={i.id} className="flex items-center gap-2 mb-2">
            <img src={i.imageUrl} className="w-10 h-10 rounded" />
            <span className="text-sm flex-1">{i.name}</span>
            <button onClick={() => removeItem(i.id)} className="text-red-500">×</button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Recommendations

```tsx
// webapp/src/components/Recommendations.tsx
import { useEffect, useState } from 'react';
import { useStore } from '../store';

export function Recommendations() {
  const { selectedItems, shownIds, getNextCategories, addItem, markShown } = useStore();
  const [items, setItems] = useState<any[]>([]);
  
  const categories = getNextCategories();
  const lastItem = selectedItems.at(-1);
  
  useEffect(() => {
    if (!lastItem || !categories.length) return;
    
    fetch('http://localhost:8000/api/recommend/complementary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        item_id: lastItem.id,
        categories,
        exclude_ids: [...shownIds],
      }),
    })
      .then((r) => r.json())
      .then((d) => {
        setItems(d.items);
        markShown(d.items.map((i: any) => i.id));
      });
  }, [lastItem?.id, categories.join()]);
  
  if (!categories.length) {
    return <p className="text-center py-4">✨ Look complete!</p>;
  }
  
  return (
    <div>
      <h3 className="font-semibold mb-3">Complete the look</h3>
      <div className="flex gap-3 overflow-x-auto pb-2">
        {items.map((i) => (
          <button key={i.id} onClick={() => addItem(i)} className="w-24 flex-shrink-0">
            <img src={i.imageUrl} className="rounded-lg" />
            <p className="text-xs truncate">{i.name}</p>
            <p className="text-xs text-gray-500">€{i.price}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
```

---

## Scripts

### Scrape

```python
# scripts/scrape.py
from scrapers.registry import get_scraper
import json

scraper = get_scraper("reaven")
items = scraper.scrape_all()

with open("data/catalog/reaven.json", "w") as f:
    json.dump([i.__dict__ for i in items], f, indent=2)

print(f"Scraped {len(items)} items")
```

### Embed

```python
# scripts/embed.py
from api.services.embeddings import EmbeddingService
from api.services.vector_store import VectorStore
from PIL import Image
import httpx, json
from io import BytesIO

emb = EmbeddingService()
store = VectorStore()
store.create_collection()

with open("data/catalog/reaven.json") as f:
    items = json.load(f)

for item in items:
    img = Image.open(BytesIO(httpx.get(item["image_url"]).content))
    vec = emb.embed_image(img)
    store.upsert(item["id"], vec.tolist(), item)
    print(f"✓ {item['name']}")
```

---

## Dependencies

```txt
# requirements.txt
fastapi>=0.104.0
uvicorn>=0.24.0
torch>=2.0.0
transformers>=4.35.0
diffusers>=0.21.0
qdrant-client>=1.6.0
httpx>=0.25.0
pillow>=10.0.0
python-multipart>=0.0.6
fashion-clip>=0.3.0
```

---

## Docker

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports: ["8000:8000"]
    depends_on: [qdrant]
    
  webapp:
    build: ./webapp
    ports: ["3000:3000"]
    
  qdrant:
    image: qdrant/qdrant
    ports: ["6333:6333"]
```

---

## Adding New Sites

1. Create `scrapers/{site}.py` with `BaseScraper`
2. Add to `scrapers/registry.py`
3. Run `scrape.py` and `embed.py`

**Planned**: Reaven ✓, ASOS, Zara, H&M
