import axiosClient from './axiosClient';

export interface ResourceItem {
  title: string;
  url: string;
  doc_type: string;
}

export interface ResourceListResponse {
  resources: ResourceItem[];
}

export const resourceApi = {
  getResources: (skillId: string, phase?: string, techniqueId?: string) => {
    const params = new URLSearchParams();
    params.append('skill_id', skillId);
    if (phase) params.append('phase', phase);
    if (techniqueId) params.append('technique_id', techniqueId);
    return axiosClient.get<ResourceListResponse>(`/resources?${params.toString()}`);
  },
};
