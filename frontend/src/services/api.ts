import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const client = axios.create({ baseURL: API_BASE_URL, timeout: 120000 })
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('plagiarism_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
client.interceptors.response.use(undefined, (error) => {
  if (axios.isAxiosError(error) && error.response?.status === 401) {
    localStorage.removeItem('plagiarism_token')
    localStorage.removeItem('plagiarism_user')
    window.dispatchEvent(new CustomEvent('plagiarism:session-expired'))
    error.message = 'Your session expired. Please sign in again.'
  }
  return Promise.reject(error)
})
export function errorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) return 'Your session expired. Please sign in again.'
    return error.response?.data?.detail || error.message
  }
  return error instanceof Error ? error.message : 'Something went wrong'
}
export type AuthResponse = { access_token?: string; user?: { name?: string } }
export type Analysis = { id: string; status: string; document_name?: string; created_at?: string; similarity_percentage?: number; direct_match_percentage?: number; matching_passages?: Array<{ source?: string; text: string; source_text?: string; score?: number; match_type?: string }>; document_text?: string; document_metadata?: { word_count?: number; character_count?: number; file_size_bytes?: number; page_count?: number | null }; source_categories?: Record<string, Array<{ name?: string; source_id?: string; passage_count?: number }>>; match_groups?: Record<string, string | number | null>; filters?: { applied?: string[]; bibliography?: boolean; quoted_text?: boolean; cited_text?: boolean; small_matches?: boolean }; integrity_flags?: Array<{ category: string; severity: string; location: string; description?: string; evidence?: string }>; processing?: { corpus_scope?: string; calculation_methodology?: string } }
export async function loginUser(email: string, password: string) { return (await client.post<AuthResponse>('/auth/login', { email, password })).data }
export async function registerUser(name: string, email: string, password: string) { return (await client.post<AuthResponse>('/auth/register', { name, email, password })).data }
export async function getDashboard() { return (await client.get('/dashboard')).data }
export async function getHistory() { return (await client.get<Analysis[]>('/analyses')).data }
export async function getAnalysis(id: string) { return (await client.get<Analysis>(`/analyses/${id}`)).data }
export async function analyzeText(payload: { text: string; options: Record<string, boolean> }) { return (await client.post<Analysis>('/analyses/text', payload)).data }
export async function analyzeDocument(file: File, options: Record<string, boolean>) { const form = new FormData(); form.append('file', file); form.append('options', JSON.stringify(options)); return (await client.post<Analysis>('/analyses/document', form)).data }
export async function compareTexts(a: string, b: string) { return (await client.post<Analysis>('/comparisons/text', { text_a: a, text_b: b })).data }
export async function downloadReport(id: string) { return (await client.get(`/analyses/${id}/report`, { responseType: 'blob' })).data as Blob }
