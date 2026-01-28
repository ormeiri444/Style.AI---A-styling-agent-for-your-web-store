'use client';

import { useState } from 'react';
import { CatalogItem } from '@/types';
import ClothingCard from './ClothingCard';

interface CatalogPanelProps {
  items: CatalogItem[];
  onSelectItem: (item: CatalogItem) => void;
  selectedItemId?: string;
  disabledCategories?: string[];
}

const CATEGORIES = [
  { value: '', label: 'All' },
  { value: 'upper_body', label: 'Tops' },
  { value: 'lower_body', label: 'Bottoms' },
  { value: 'shoes', label: 'Shoes' },
];

const GENDERS = [
  { value: '', label: 'All' },
  { value: 'women', label: 'Women' },
  { value: 'men', label: 'Men' },
];

export default function CatalogPanel({
  items,
  onSelectItem,
  selectedItemId,
  disabledCategories = [],
}: CatalogPanelProps) {
  const [categoryFilter, setCategoryFilter] = useState('');
  const [genderFilter, setGenderFilter] = useState('');

  const filteredItems = items.filter((item) => {
    if (categoryFilter && item.category !== categoryFilter) return false;
    if (genderFilter && item.gender !== genderFilter) return false;
    return true;
  });

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-2 flex-wrap">
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="text-sm border rounded px-2 py-1"
        >
          {CATEGORIES.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>
        <select
          value={genderFilter}
          onChange={(e) => setGenderFilter(e.target.value)}
          className="text-sm border rounded px-2 py-1"
        >
          {GENDERS.map((g) => (
            <option key={g.value} value={g.value}>
              {g.label}
            </option>
          ))}
        </select>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-[400px] overflow-y-auto">
        {filteredItems.map((item) => (
          <ClothingCard
            key={item.id}
            item={item}
            onSelect={onSelectItem}
            isSelected={item.id === selectedItemId}
            disabled={disabledCategories.includes(item.category)}
          />
        ))}
      </div>
    </div>
  );
}
