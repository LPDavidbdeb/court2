import React, { useEffect, useState } from 'react';
import api from '../services/api';
import type { PhotoDocumentSchema } from '../types/api';
import { Card } from './ui/card';
import { Skeleton } from './ui/skeleton';

const EvidenceGallery: React.FC = () => {
  const [photos, setPhotos] = useState<PhotoDocumentSchema[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<PhotoDocumentSchema[]>('/photos/')
      .then(res => setPhotos(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Skeleton className="h-40 w-full" />;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {photos.map(photo => (
        <Card key={photo.id} className="p-2 flex flex-col items-center">
          {photo.public_url && (
            <img src={photo.public_url} alt={photo.file_name} className="w-full h-40 object-cover rounded" />
          )}
          <div className="mt-2 text-xs text-gray-600">{photo.file_name}</div>
        </Card>
      ))}
    </div>
  );
};

export default EvidenceGallery;
