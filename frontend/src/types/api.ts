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
