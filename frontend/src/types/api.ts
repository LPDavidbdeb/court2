// TypeScript interfaces mirroring backend Pydantic schemas

export interface PhotoDocumentSchema {
  id: number;
  public_url?: string;
  created_at?: string;
  updated_at?: string;
  file_name: string;
  file_size?: number;
  width?: number;
  height?: number;
  image_format?: string;
  image_mode?: string;
  artist?: string;
  datetime_original?: string;
  gps_latitude?: number;
  gps_longitude?: number;
  make?: string;
  model?: string;
  iso_speed?: number;
  exposure_time?: string;
  f_number?: number;
  focal_length?: number;
  lens_model?: string;
}

export interface EventSchema {
  id: number;
  public_url?: string;
  created_at?: string;
  updated_at?: string;
  date: string;
  explanation: string;
  email_quote?: string;
  linked_email_id?: number;
  parent_id?: number;
}

export interface EventDetailSchema extends EventSchema {
  linked_photos: PhotoDocumentSchema[];
}

