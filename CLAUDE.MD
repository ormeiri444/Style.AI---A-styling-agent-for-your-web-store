# CLAUDE.md - AI Fashion Stylist POC

## Project Overview

A local web application that allows users to:
1. Upload a full-body photo of themselves
2. Upload a clothing item image
3. See themselves wearing that item (virtual try-on via Gemini)
4. Get AI-powered suggestions for complementary items to complete the look
5. Click on suggested items and see them added to their virtual outfit

## Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React/Next.js)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Image Upload │  │  Try-On    │  │  Recommendation Panel   │  │
│  │   Section   │  │   Display   │  │   (Clickable Items)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI/Python)                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  Try-On Service │  │ Recommendation   │  │  Session/State │  │
│  │  (Gemini Pro 3) │  │ Service (Gemini) │  │   Management   │  │
│  └─────────────────┘  └──────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Google Gemini API                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ gemini-3-pro-image-preview                                  ││
│  │ - Virtual try-on (image editing with multiple references)   ││
│  │ - Up to 14 reference images (5 humans + 6 objects)         ││
│  │ - Multi-turn editing for building outfits                   ││
│  │ - High-res output (1K/2K/4K)                               ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ gemini-3-flash-preview (FREE tier)                          ││
│  │ - Outfit analysis and recommendations                       ││
│  │ - Style reasoning                                           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router) or React + Vite
- **Styling**: Tailwind CSS
- **State Management**: React Context or Zustand
- **Image Handling**: react-dropzone for uploads

### Backend
- **Framework**: FastAPI (Python)
- **Virtual Try-On**: Google Gemini 3 Pro Image Preview
- **AI Recommendations**: Google Gemini 3 Flash (free tier)
- **Async Operations**: asyncio + httpx
- **SDK**: `google-genai` Python package

### External Services

#### 1. Virtual Try-On (Gemini 3 Pro Image Preview)
- **Model**: `gemini-3-pro-image-preview`
- **Cost**: 
  - Input: ~$0.0011 per image
  - Output: ~$0.134 per 1K/2K image, ~$0.24 per 4K image
  - **Total per try-on: ~$0.14**
- **Key Features**:
  - Up to 14 reference images (5 humans + 6 objects)
  - Multi-turn editing for iterative outfit building
  - "Thinking mode" for complex reasoning
  - High-resolution output (1K, 2K, 4K)
- **Inputs**:
  - Human full-body image
  - Clothing item image(s)
  - Text prompt describing the task
- **Output**: Generated image of person wearing the clothing

#### 2. Outfit Recommendations (Gemini 3 Flash Preview)
- **Model**: `gemini-3-flash-preview`
- **Cost**: FREE tier available
- **Use Case**: Analyze current outfit and suggest complementary items
- **Inputs**: 
  - Current outfit image
  - Available catalog items
  - User preferences (optional)
- **Output**: Structured JSON with recommended items and reasons

## Directory Structure
```
fashion-stylist-poc/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Environment variables
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── tryon.py         # Virtual try-on endpoints
│   │   │   └── recommend.py     # Recommendation endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── gemini_tryon.py      # Gemini image generation
│   │   │   ├── gemini_recommend.py  # Gemini recommendations
│   │   │   └── catalog_service.py   # Clothing catalog management
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py       # Pydantic models
│   │   └── data/
│   │       ├── catalog.json     # Sample clothing catalog
│   │       └── catalog_images/  # Catalog item images
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # Main page
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ImageUploader.tsx
│   │   │   ├── TryOnDisplay.tsx
│   │   │   ├── RecommendationPanel.tsx
│   │   │   ├── ClothingCard.tsx
│   │   │   └── OutfitBuilder.tsx
│   │   ├── hooks/
│   │   │   ├── useTryOn.ts
│   │   │   └── useRecommendations.ts
│   │   ├── services/
│   │   │   └── api.ts           # Backend API calls
│   │   └── types/
│   │       └── index.ts
│   ├── package.json
│   └── tailwind.config.js
├── CLAUDE.md
└── README.md
```

## API Endpoints

### Backend API
```
POST /api/tryon
  - Body: { human_image: base64, garment_image: base64, garment_description: string, category: string }
  - Response: { result_image: base64, outfit_state: object }

POST /api/tryon/add-item
  - Body: { current_outfit_image: base64, new_item_image: base64, item_description: string }
  - Response: { result_image: base64, outfit_state: object }

POST /api/recommend
  - Body: { current_outfit_image: base64, worn_items: array, preferences?: object }
  - Response: { recommendations: [{ id, name, image_url, category, reason }] }

GET /api/catalog
  - Query: ?category=tops|bottoms|shoes|accessories
  - Response: { items: [...] }
```

## Core Algorithms

### 1. Virtual Try-On with Gemini
```python
from google import genai
from google.genai import types
from PIL import Image
import base64
import io

async def perform_tryon(
    human_image: bytes, 
    garment_image: bytes, 
    garment_description: str,
    category: str = "upper_body"
) -> bytes:
    """
    Use Gemini 3 Pro Image Preview for virtual try-on.
    Combines person photo with clothing item to generate try-on result.
    """
    client = genai.Client()
    
    # Convert bytes to PIL Images
    human_img = Image.open(io.BytesIO(human_image))
    garment_img = Image.open(io.BytesIO(garment_image))
    
    prompt = f"""
    You are a professional fashion virtual try-on system.
    
    Task: Generate a realistic image of the person in the first image 
    wearing the {category} clothing item shown in the second image.
    
    Clothing description: {garment_description}
    
    Requirements:
    - Maintain the person's exact face, body shape, pose, and proportions
    - Apply the clothing item naturally, accounting for body position
    - Preserve realistic lighting and shadows
    - Keep the original background
    - The clothing should fit naturally on the person's body
    - Maintain high image quality and realism
    """
    
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[prompt, human_img, garment_img],
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio="3:4",  # Portrait orientation
                image_size="2K"
            )
        )
    )
    
    # Extract generated image
    for part in response.parts:
        if part.inline_data is not None:
            result_image = part.as_image()
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            result_image.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
    
    raise Exception("No image generated")
```

### 2. Multi-Turn Outfit Building
```python
async def add_item_to_outfit(
    current_outfit_image: bytes,
    new_item_image: bytes,
    item_description: str,
    worn_items: list[str]
) -> bytes:
    """
    Add another clothing item to an existing outfit using multi-turn editing.
    """
    client = genai.Client()
    
    current_img = Image.open(io.BytesIO(current_outfit_image))
    new_item_img = Image.open(io.BytesIO(new_item_image))
    
    prompt = f"""
    The person in the first image is currently wearing: {', '.join(worn_items)}.
    
    Task: Add the clothing item from the second image to complete their outfit.
    
    New item description: {item_description}
    
    Requirements:
    - Keep everything about the current outfit exactly the same
    - Add ONLY the new item to the appropriate body part
    - Maintain realistic proportions and fit
    - Preserve the person's identity and pose
    - Ensure the new item coordinates well with existing clothing
    """
    
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[prompt, current_img, new_item_img],
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio="3:4",
                image_size="2K"
            )
        )
    )
    
    for part in response.parts:
        if part.inline_data is not None:
            result_image = part.as_image()
            img_byte_arr = io.BytesIO()
            result_image.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
    
    raise Exception("No image generated")
```

### 3. Outfit Recommendations (Free Tier)
```python
async def get_recommendations(
    outfit_image: bytes, 
    worn_items: list[dict],
    catalog: list[dict]
) -> list[dict]:
    """
    Use Gemini Flash (free tier) to analyze outfit and recommend items.
    """
    client = genai.Client()
    
    outfit_img = Image.open(io.BytesIO(outfit_image))
    
    # Format catalog for context
    catalog_text = "\\n".join([
        f"- ID: {item['id']}, Name: {item['name']}, Category: {item['category']}, "
        f"Color: {item['color']}, Style: {', '.join(item['style'])}"
        for item in catalog
    ])
    
    prompt = f"""
    Analyze this outfit image and recommend complementary clothing items.
    
    Currently wearing:
    {json.dumps(worn_items, indent=2)}
    
    Available items in catalog:
    {catalog_text}
    
    Based on:
    1. Color harmony and coordination
    2. Style consistency
    3. Occasion appropriateness
    4. Fashion principles
    
    Recommend 3-5 items that would complete or enhance this look.
    
    Return ONLY valid JSON in this exact format:
    {{
        "recommendations": [
            {{
                "id": "item_id",
                "reason": "Brief explanation of why this item complements the outfit"
            }}
        ],
        "style_analysis": "Brief description of the current outfit's style"
    }}
    """
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[outfit_img, prompt],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT']
        )
    )
    
    # Parse JSON response
    import json
    result = json.loads(response.text)
    
    # Enrich with catalog data
    enriched = []
    for rec in result["recommendations"]:
        item = next((i for i in catalog if i["id"] == rec["id"]), None)
        if item:
            enriched.append({
                **item,
                "reason": rec["reason"]
            })
    
    return enriched
```

### 4. Session State Management
```python
from dataclasses import dataclass, field
from typing import Optional
import uuid

@dataclass
class ClothingItem:
    id: str
    name: str
    category: str  # "upper_body", "lower_body", "shoes", "accessories"
    image_url: str
    description: str

@dataclass
class OutfitSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    base_human_image: Optional[bytes] = None
    current_outfit_image: Optional[bytes] = None
    worn_items: list[ClothingItem] = field(default_factory=list)
    
    def add_item(self, item: ClothingItem, new_outfit_image: bytes):
        """Add item to outfit and update the current image."""
        self.worn_items.append(item)
        self.current_outfit_image = new_outfit_image
    
    def get_worn_categories(self) -> list[str]:
        """Get list of categories already worn."""
        return [item.category for item in self.worn_items]
    
    def can_add_category(self, category: str) -> bool:
        """Check if we can add an item of this category."""
        # Allow multiple accessories, but only one of each other category
        if category == "accessories":
            return True
        return category not in self.get_worn_categories()

# In-memory session storage (use Redis for production)
sessions: dict[str, OutfitSession] = {}
```

## Sample Clothing Catalog Structure
```json
{
  "items": [
    {
      "id": "top_001",
      "name": "White Cotton T-Shirt",
      "category": "upper_body",
      "subcategory": "t-shirt",
      "color": "white",
      "style": ["casual", "minimalist", "streetwear"],
      "image_path": "catalog_images/top_001.jpg",
      "description": "Classic white cotton crew neck t-shirt"
    },
    {
      "id": "top_002",
      "name": "Navy Blue Oxford Shirt",
      "category": "upper_body",
      "subcategory": "button-up",
      "color": "navy",
      "style": ["smart-casual", "preppy", "business-casual"],
      "image_path": "catalog_images/top_002.jpg",
      "description": "Navy blue oxford button-up shirt"
    },
    {
      "id": "bottom_001",
      "name": "Blue Denim Jeans",
      "category": "lower_body",
      "subcategory": "jeans",
      "color": "blue",
      "style": ["casual", "streetwear"],
      "image_path": "catalog_images/bottom_001.jpg",
      "description": "Classic slim fit blue denim jeans"
    },
    {
      "id": "bottom_002",
      "name": "Khaki Chinos",
      "category": "lower_body",
      "subcategory": "chinos",
      "color": "khaki",
      "style": ["smart-casual", "preppy", "business-casual"],
      "image_path": "catalog_images/bottom_002.jpg",
      "description": "Tailored khaki chino pants"
    },
    {
      "id": "shoes_001",
      "name": "White Sneakers",
      "category": "shoes",
      "subcategory": "sneakers",
      "color": "white",
      "style": ["casual", "streetwear", "minimalist"],
      "image_path": "catalog_images/shoes_001.jpg",
      "description": "Clean white leather sneakers"
    },
    {
      "id": "shoes_002",
      "name": "Brown Leather Loafers",
      "category": "shoes",
      "subcategory": "loafers",
      "color": "brown",
      "style": ["smart-casual", "preppy", "business-casual"],
      "image_path": "catalog_images/shoes_002.jpg",
      "description": "Classic brown leather penny loafers"
    }
  ]
}
```

## Environment Variables
```env
# Backend (.env)
GOOGLE_API_KEY=AIza_your_gemini_api_key_here

# Optional settings
IMAGE_OUTPUT_SIZE=2K  # 1K, 2K, or 4K
MAX_CATALOG_ITEMS=50

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Requirements

### Backend (requirements.txt)
```
fastapi>=0.109.0
uvicorn>=0.27.0
python-multipart>=0.0.6
google-genai>=0.3.0
Pillow>=10.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### Frontend (package.json dependencies)
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-dropzone": "^14.2.0",
    "zustand": "^4.4.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.0",
    "typescript": "^5.0.0",
    "@types/react": "^18.2.0"
  }
}
```

## Implementation Phases

### Phase 1: Basic Try-On (MVP) - Day 1-2
1. Set up FastAPI backend with Gemini integration
2. Create simple React frontend with dual image upload
3. Implement basic try-on flow (upload person + garment → see result)
4. Test with sample images
5. Handle loading states and errors

### Phase 2: Recommendations - Day 2-3
1. Create sample clothing catalog (15-20 items with images)
2. Implement recommendation endpoint using Gemini Flash (free)
3. Build recommendation panel UI
4. Display recommended items as clickable cards

### Phase 3: Interactive Outfit Building - Day 3-4
1. Add "add to outfit" functionality
2. Track outfit state (what items are being worn)
3. Chain try-on calls (add pants on top of shirt result)
4. Update recommendations based on current outfit
5. Prevent adding duplicate categories

### Phase 4: Polish - Day 4-5
1. Improve UI/UX with better layouts
2. Add outfit history sidebar
3. Add "reset outfit" functionality
4. Optimize for mobile
5. Add error recovery and retry logic

## Cost Estimation (POC Budget: $100)

| Operation | Cost | Estimated Count | Total |
|-----------|------|-----------------|-------|
| Try-on (2K output) | ~$0.14 | 500 operations | $70 |
| Recommendations (Flash) | FREE | Unlimited | $0 |
| **Total** | | | **~$70** |

**Remaining budget**: ~$30 buffer for experimentation and iterations

## Prompt Engineering Tips

### For Virtual Try-On
- Be explicit about maintaining the person's identity
- Specify clothing category clearly
- Mention preserving pose, lighting, and background
- Request realistic fabric draping and fit

### For Recommendations
- Provide structured catalog data
- Ask for JSON output format explicitly
- Include style vocabulary (casual, formal, streetwear, etc.)
- Request reasoning for each recommendation

## Key Technical Considerations

### Image Quality
- Accept common formats: JPEG, PNG, WebP
- Recommend portrait orientation (3:4) for full-body shots
- Compress large images before sending (max ~4MB)
- Use 2K output for balance of quality vs cost

### Error Handling
- Gemini may refuse certain images (content policy)
- Implement retry logic with exponential backoff
- Cache successful results
- Provide meaningful error messages to users

### Performance
- Try-on generation takes 5-15 seconds
- Show skeleton/loading state during generation
- Consider WebSocket for progress updates
- Pre-load catalog images for instant recommendations

## Testing Strategy

1. **Unit Tests**: Mock Gemini responses, test business logic
2. **Integration Tests**: Test full API flow with real Gemini calls
3. **Visual Testing**: Manual verification of try-on quality
4. **Edge Cases**: Test with various body types, poses, clothing styles

## Useful Resources

- [Gemini API Image Generation Docs](https://ai.google.dev/gemini-api/docs/image-generation)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Google GenAI Python SDK](https://github.com/google/genai-python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)