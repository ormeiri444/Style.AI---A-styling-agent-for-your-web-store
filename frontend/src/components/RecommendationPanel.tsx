'use client';

import { RecommendationItem } from '@/types';

interface RecommendationPanelProps {
  recommendations: RecommendationItem[];
  onSelectRecommendation: (item: RecommendationItem) => void;
  isLoading: boolean;
}

export default function RecommendationPanel({
  recommendations,
  onSelectRecommendation,
  isLoading,
}: RecommendationPanelProps) {
  if (isLoading) {
    return (
      <div className="border rounded-lg p-4 bg-gray-50">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Recommendations</h3>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className="border rounded-lg p-4 bg-gray-50">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Recommendations</h3>
        <p className="text-gray-400 text-sm text-center py-4">
          Complete a try-on to get recommendations
        </p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Recommended Items</h3>
      <div className="space-y-3">
        {recommendations.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelectRecommendation(item)}
            className="w-full flex gap-3 p-2 border border-gray-200 rounded-lg bg-white hover:border-blue-300 transition-colors text-left"
          >
            <div className="w-16 h-16 bg-gray-100 rounded overflow-hidden flex-shrink-0">
              <img
                src={`http://localhost:8000/static/${item.image_url}`}
                alt={item.name}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">{item.name}</p>
              <p className="text-xs text-gray-500">{item.category}</p>
              <p className="text-xs text-blue-600 mt-1 line-clamp-2">{item.reason}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
