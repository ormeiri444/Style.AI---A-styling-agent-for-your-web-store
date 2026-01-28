'use client';

import { CatalogItem } from '@/types';

interface ClothingCardProps {
  item: CatalogItem;
  onSelect: (item: CatalogItem) => void;
  isSelected?: boolean;
  disabled?: boolean;
}

export default function ClothingCard({
  item,
  onSelect,
  isSelected = false,
  disabled = false,
}: ClothingCardProps) {
  const imageUrl = `http://localhost:8000/static/${item.image_path}`;

  return (
    <button
      onClick={() => !disabled && onSelect(item)}
      disabled={disabled}
      className={`border rounded-lg p-2 transition-all text-left ${
        isSelected
          ? 'border-blue-500 ring-2 ring-blue-200'
          : 'border-gray-200 hover:border-gray-300'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      <div className="aspect-square bg-gray-100 rounded mb-2 overflow-hidden">
        <img
          src={imageUrl}
          alt={item.name}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/placeholder.png';
          }}
        />
      </div>
      <p className="text-xs font-medium text-gray-800 truncate" title={item.name}>
        {item.brand}
      </p>
      <p className="text-xs text-gray-500 truncate">{item.category}</p>
    </button>
  );
}
