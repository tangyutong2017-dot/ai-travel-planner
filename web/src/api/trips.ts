import type { Itinerary } from '../types/itinerary'
import type { CreateTripPayload, CreateTripResponse, GetTripsParams, Trip, TripListResponse } from '../types/trip'
import { apiDelete, apiGet, apiPatch, apiPost } from './client'

type ApiTrip = Omit<Trip, 'status'> & {
  status: 'planned' | 'completed'
}

type ApiTripListResponse = Omit<TripListResponse, 'items'> & {
  items: ApiTrip[]
}

const apiStatusToDisplay: Record<ApiTrip['status'], Trip['status']> = {
  planned: '计划中',
  completed: '已完成',
}

const toDisplayTrip = (trip: ApiTrip): Trip => ({
  ...trip,
  status: apiStatusToDisplay[trip.status],
})

export async function getTrips(params: GetTripsParams = {}): Promise<TripListResponse> {
  const query = new URLSearchParams()

  if (params.status) query.set('status', params.status)
  if (params.sort) query.set('sort', params.sort)
  if (params.keyword) query.set('keyword', params.keyword)

  const data = await apiGet<ApiTripListResponse>(`/api/trips${query.size ? `?${query.toString()}` : ''}`)
  return {
    ...data,
    items: data.items.map(toDisplayTrip),
  }
}

export async function createTrip(payload: CreateTripPayload): Promise<{ tripId: string }> {
  return apiPost<{ tripId: string }, CreateTripPayload>('/api/trips', payload)
}

export async function startTripGeneration(tripId: string): Promise<CreateTripResponse> {
  return apiPost<CreateTripResponse>(`/api/trips/${tripId}/generate`)
}

export async function getTripDetail(tripId: string): Promise<Itinerary> {
  return apiGet<Itinerary>(`/api/trips/${tripId}`)
}

export async function deleteTrip(tripId: string): Promise<{ tripId: string }> {
  return apiDelete<{ tripId: string }>(`/api/trips/${tripId}`)
}

export async function updateTripName(tripId: string, name: string): Promise<Trip> {
  return apiPatch<Trip, { name: string }>(`/api/trips/${tripId}`, { name })
}

export async function deleteTripItem(tripId: string, day: number, itemId: string): Promise<Itinerary> {
  return apiDelete<Itinerary>(`/api/trips/${tripId}/days/${day}/items/${itemId}`)
}

export type UpdateTripItemPayload = {
  title?: string
  startTime?: string
  endTime?: string
  type?: string
  durationLabel?: string
  cost?: number
  reason?: string
}

export async function updateTripItem(
  tripId: string,
  day: number,
  itemId: string,
  payload: UpdateTripItemPayload,
): Promise<Itinerary> {
  return apiPatch<Itinerary, UpdateTripItemPayload>(`/api/trips/${tripId}/days/${day}/items/${itemId}`, payload)
}

export type EditTripPayload = {
  instruction: string
  activeDay?: number
}

export type EditTripResponse = {
  message: string
  itinerary: Itinerary
}

export async function editTrip(tripId: string, payload: EditTripPayload): Promise<EditTripResponse> {
  return apiPost<EditTripResponse, EditTripPayload>(`/api/trips/${tripId}/edit`, payload)
}
