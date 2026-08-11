import type { AgentJob } from '../types/job'
import { apiGet } from './client'

export async function getJobStatus(jobId: string, _tripId: string): Promise<AgentJob> {
  return apiGet<AgentJob>(`/api/jobs/${jobId}`)
}
