'use client';

import { useState, useEffect } from 'react';
import ImageUploader from '@/components/ImageUploader';
import TryOnDisplay from '@/components/TryOnDisplay';
import CatalogPanel from '@/components/CatalogPanel';
import RecommendationPanel from '@/components/RecommendationPanel';
import { CatalogItem, RecommendationItem } from '@/types';
import { performTryOn, addItemToOutfit, getRecommendations, getCatalog, urlToBase64 } from '@/services/api';

export default function Home() {
  const [humanImage, setHumanImage] = useState<string | null>(null);
  const [resultImage, setResultImage] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<CatalogItem | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [wornItems, setWornItems] = useState<Array<{ category: string; name: string; description: string }>>([]);
  const [isLoadingTryOn, setIsLoadingTryOn] = useState(false);
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCatalog().then(setCatalog).catch(console.error);
  }, []);

  const handleTryOn = async () => {
    if (!humanImage || !selectedItem) return;

    setIsLoadingTryOn(true);
    setError(null);

    try {
      const garmentImageB64 = await urlToBase64(
        `http://localhost:8000/static/${selectedItem.image_path}`
      );

      let result;
      if (wornItems.length === 0) {
        result = await performTryOn({
          human_image: humanImage,
          garment_image: garmentImageB64,
          garment_description: selectedItem.description,
          category: selectedItem.category,
        });
      } else {
        result = await addItemToOutfit(
          resultImage!,
          garmentImageB64,
          selectedItem.description
        );
      }

      setResultImage(result.result_image);
      setWornItems([
        ...wornItems,
        {
          category: selectedItem.category,
          name: selectedItem.name,
          description: selectedItem.description,
        },
      ]);
      setSelectedItem(null);

      // Fetch recommendations
      setIsLoadingRecs(true);
      try {
        const recs = await getRecommendations(result.result_image, [
          ...wornItems,
          { category: selectedItem.category, name: selectedItem.name },
        ]);
        setRecommendations(recs);
      } catch (e) {
        console.error('Failed to get recommendations:', e);
      } finally {
        setIsLoadingRecs(false);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Try-on failed');
      console.error(e);
    } finally {
      setIsLoadingTryOn(false);
    }
  };

  const handleRecommendationClick = async (item: RecommendationItem) => {
    const catalogItem = catalog.find((c) => c.id === item.id);
    if (catalogItem) {
      setSelectedItem(catalogItem);
    }
  };

  const handleReset = () => {
    setResultImage(null);
    setWornItems([]);
    setRecommendations([]);
    setSelectedItem(null);
  };

  const wornCategories = wornItems.map((w) => w.category);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">AI Fashion Stylist</h1>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Upload & Catalog */}
          <div className="space-y-4">
            <div className="bg-white rounded-lg p-4 shadow">
              <ImageUploader
                label="Upload Your Photo"
                image={humanImage}
                onImageChange={setHumanImage}
              />
            </div>

            <div className="bg-white rounded-lg p-4 shadow">
              <h2 className="text-sm font-medium text-gray-700 mb-3">Select Clothing</h2>
              <CatalogPanel
                items={catalog}
                onSelectItem={setSelectedItem}
                selectedItemId={selectedItem?.id}
                disabledCategories={wornCategories}
              />
            </div>
          </div>

          {/* Center Column: Try-On Result */}
          <div className="space-y-4">
            <div className="bg-white rounded-lg p-4 shadow">
              <TryOnDisplay image={resultImage} isLoading={isLoadingTryOn} />

              <div className="mt-4 flex gap-2">
                <button
                  onClick={handleTryOn}
                  disabled={!humanImage || !selectedItem || isLoadingTryOn}
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {wornItems.length === 0 ? 'Try On' : 'Add to Outfit'}
                </button>
                {wornItems.length > 0 && (
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Reset
                  </button>
                )}
              </div>

              {wornItems.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-2">Currently wearing:</p>
                  <div className="flex flex-wrap gap-1">
                    {wornItems.map((item, i) => (
                      <span
                        key={i}
                        className="text-xs bg-gray-100 px-2 py-1 rounded"
                      >
                        {item.name.slice(0, 30)}...
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Recommendations */}
          <div className="bg-white rounded-lg p-4 shadow">
            <RecommendationPanel
              recommendations={recommendations}
              onSelectRecommendation={handleRecommendationClick}
              isLoading={isLoadingRecs}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
