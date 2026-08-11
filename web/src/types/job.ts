export type AgentJobStatus = 'queued' | 'running' | 'succeeded' | 'failed'

export type AgentJob = {
  jobId: string
  tripId: string
  status: AgentJobStatus
  progress: number
  message: string
}

