export interface ExhibitableBase {
  id: number;
  public_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ProducedExhibit extends ExhibitableBase {
  case_id: number;
  exhibit_type: string;
  parties?: string;
  label?: string;
  date_display?: string;
  description?: string;
}

export interface ProtagonistEmail {
  id?: number;
  email_address: string;
  description?: string;
}

export interface Protagonist {
  id: number;
  first_name: string;
  last_name?: string;
  role: string;
  linkedin_url?: string;
  created_at: string;
  updated_at: string;
  emails: ProtagonistEmail[];
}

export interface ProtagonistCreate {
  first_name: string;
  last_name?: string;
  role: string;
  linkedin_url?: string;
  emails: ProtagonistEmail[];
}

export interface PerjuryContestation {
  id: number;
  case_id: number;
  title: string;
  final_sec1_declaration: string;
  final_sec2_proof: string;
  final_sec3_mens_rea: string;
  final_sec4_intent: string;
  updated_at: string;
}

export interface LegalCase {
  id: number;
  title: string;
  created_at: string;
}

export interface LegalCaseDetail extends LegalCase {
  contestations: PerjuryContestation[];
  produced_exhibits: ProducedExhibit[];
}

// --- Batch 2 Interfaces ---

export interface Document extends ExhibitableBase {
  title: string;
  author?: Protagonist;
  document_original_date?: string;
  solemn_declaration?: string;
  source_type: 'REPRODUCED' | 'PRODUCED';
  file_source?: string;
}

export interface DocumentCreate {
  title: string;
  author_id?: number;
  document_original_date?: string;
  solemn_declaration?: string;
  source_type: 'REPRODUCED' | 'PRODUCED';
}

export interface Statement {
  id: number;
  text?: string;
  is_true: boolean;
  is_falsifiable?: boolean;
  created_at: string;
}

export interface Email extends ExhibitableBase {
  thread_id: number;
  message_id: string;
  subject?: string;
  sender?: string;
  date_sent?: string;
  body_plain_text?: string;
  sender_protagonist?: Protagonist;
  recipient_protagonists: Protagonist[];
}

export interface EmailThread {
  id: number;
  thread_id: string;
  subject?: string;
  protagonist?: Protagonist;
  updated_at: string;
}

export interface EmailThreadDetail extends EmailThread {
  emails: Email[];
}

export interface EmailQuote extends ExhibitableBase {
  email_id: number;
  quote_text: string;
  full_sentence: string;
}

export interface PDFDocument extends ExhibitableBase {
  title: string;
  author?: Protagonist;
  document_date?: string;
  file?: string;
  ai_analysis?: string;
}

export interface PDFQuote extends ExhibitableBase {
  pdf_document_id: number;
  quote_text: string;
  page_number: number;
}

export interface PhotoDocumentSchema extends ExhibitableBase {
  file_name: string;
}

export interface EventSchema {
  id: number;
  date: string;
  explanation: string;
  email_quote?: string;
}
