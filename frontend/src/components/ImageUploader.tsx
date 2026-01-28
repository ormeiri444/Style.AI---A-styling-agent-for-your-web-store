'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface ImageUploaderProps {
  label: string;
  image: string | null;
  onImageChange: (base64: string) => void;
  accept?: Record<string, string[]>;
}

export default function ImageUploader({
  label,
  image,
  onImageChange,
  accept = { 'image/*': ['.png', '.jpg', '.jpeg', '.webp'] },
}: ImageUploaderProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result as string;
          const base64 = result.split(',')[1];
          onImageChange(base64);
        };
        reader.readAsDataURL(file);
      }
    },
    [onImageChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple: false,
  });

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors min-h-[200px] flex items-center justify-center ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        {image ? (
          <img
            src={`data:image/jpeg;base64,${image}`}
            alt="Uploaded"
            className="max-h-[180px] object-contain"
          />
        ) : (
          <div className="text-gray-500">
            {isDragActive ? (
              <p>Drop the image here...</p>
            ) : (
              <p>Drag & drop an image, or click to select</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
