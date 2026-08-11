export type ApiTripStatus = 'planned' | 'completed'
export type TripStatus = '计划中' | '已完成'
export type TripFilter = TripStatus | '全部'
export type TripSort = 'updatedAt_desc' | 'startDate_desc' | 'days_desc'

export type Trip = {
  id: string
  name: string
  dest: string
  days: number
  date: string
  status: TripStatus
  coverUrl?: string
  updatedAt?: string
  attractionCount?: number
}

export type TripListResponse = {
  items: Trip[]
}

export type GetTripsParams = {
  status?: ApiTripStatus
  sort?: TripSort
  keyword?: string
}

export type TravelersPayload = {
  adults: number
  children: number
  infants: number
}

export type CreateTripPayload = {
  destination: string
  startDate: string
  endDate: string
  days: number
  travelers: TravelersPayload
  budget: {
    min: number
    max: number
  }
  preferences: {
    interests: string[]
    pace: number
    transport: string[]
    accommodation: string[]
    customText: string
  }
}

export type CreateTripResponse = {
  tripId: string
  jobId: string
}

export const tripStatusToApi = (status: TripFilter): ApiTripStatus | undefined => {
  if (status === '计划中') return 'planned'
  if (status === '已完成') return 'completed'
  return undefined
}
