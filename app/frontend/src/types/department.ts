export interface ExpertDepartment {
  id: string;
  name: string;
  category_id: string;
  category_name: string | null;
  synonyms: string[];
  is_active: boolean;
  is_verified: boolean;
  expert_count: number;
  source: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExpertDepartmentCreatePayload {
  name: string;
  category_id: string;
  synonyms?: string[];
  is_verified?: boolean;
}

export interface ExpertDepartmentUpdatePayload {
  name?: string;
  category_id?: string;
  synonyms?: string[];
  is_active?: boolean;
  is_verified?: boolean;
}

export interface ExpertDepartmentBrief {
  id: string;
  name: string;
  category_id: string;
  category_name: string | null;
}

export interface DepartmentQueryParams {
  page?: number;
  size?: number;
  is_active?: boolean;
  is_verified?: boolean;
  category_id?: string;
  q?: string;
}

export interface UnmappedExpert {
  id: string;
  name: string;
  title: string | null;
  hospital: string | null;
  avatar_url: string | null;
  category_id: string | null;
  category_name: string | null;
  expertise_areas: string[];
  is_active: boolean;
  is_verified: boolean;
}
