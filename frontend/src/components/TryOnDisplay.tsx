'use client';

interface TryOnDisplayProps {
  image: string | null;
  isLoading: boolean;
}

export default function TryOnDisplay({ image, isLoading }: TryOnDisplayProps) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-gray-700">Try-On Result</label>
      <div className="border-2 border-gray-200 rounded-lg bg-gray-50 min-h-[400px] flex items-center justify-center">
        {isLoading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="text-gray-500">Generating try-on...</p>
          </div>
        ) : image ? (
          <img
            src={`data:image/png;base64,${image}`}
            alt="Try-on result"
            className="max-h-[380px] object-contain"
          />
        ) : (
          <div className="text-gray-400 text-center p-4">
            <p>Upload a photo and select a garment to see the result</p>
          </div>
        )}
      </div>
    </div>
  );
}
