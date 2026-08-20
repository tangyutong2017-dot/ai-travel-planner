import type { Itinerary, StopType, TimeSlot } from "../types/itinerary";
import type { CreateTripPayload, CreateTripResponse, GetTripsParams, Trip, TripListResponse } from "../types/trip";
import { apiDelete, apiGet, apiPatch, apiPost } from "./client";

type ApiTrip = Omit<Trip, "status"> & {
  status: "planned" | "completed";
};

type ApiTripListResponse = Omit<TripListResponse, "items"> & {
  items: ApiTrip[];
};

const apiStatusToDisplay: Record<ApiTrip["status"], Trip["status"]> = {
  planned: "计划中",
  completed: "已完成",
};

const toDisplayTrip = (trip: ApiTrip): Trip => ({
  ...trip,
  status: apiStatusToDisplay[trip.status],
});

/** 在途请求去重。
 *
 * 侧边栏「最近行程」与列表页各自加载一次，默认筛选下参数完全一致——
 * 打开首页会对同一个 URL 发两次请求（开发模式下 StrictMode 双渲染再翻倍成四次）。
 * 同一 URL 的请求尚未返回时复用同一个 Promise，返回后即清除，不做缓存——
 * 后续的重新加载仍应拿到最新数据。
 */
const inFlightTripRequests = new Map<string, Promise<TripListResponse>>();

export async function getTrips(params: GetTripsParams = {}): Promise<TripListResponse> {
  const query = new URLSearchParams();

  if (params.status) query.set("status", params.status);
  if (params.sort) query.set("sort", params.sort);
  if (params.keyword) query.set("keyword", params.keyword);

  const path = `/api/trips${query.size ? `?${query.toString()}` : ""}`;
  const pending = inFlightTripRequests.get(path);
  if (pending) return pending;

  const request = apiGet<ApiTripListResponse>(path)
    .then((data) => ({ ...data, items: data.items.map(toDisplayTrip) }))
    .finally(() => inFlightTripRequests.delete(path));

  inFlightTripRequests.set(path, request);
  return request;
}

export async function createTrip(payload: CreateTripPayload): Promise<{ tripId: string }> {
  return apiPost<{ tripId: string }, CreateTripPayload>("/api/trips", payload);
}

export async function startTripGeneration(tripId: string): Promise<CreateTripResponse> {
  return apiPost<CreateTripResponse>(`/api/trips/${tripId}/generate`);
}

export async function getTripDetail(tripId: string): Promise<Itinerary> {
  return apiGet<Itinerary>(`/api/trips/${tripId}`);
}

export async function deleteTrip(tripId: string): Promise<{ tripId: string }> {
  return apiDelete<{ tripId: string }>(`/api/trips/${tripId}`);
}

export async function updateTripName(tripId: string, name: string): Promise<Trip> {
  return apiPatch<Trip, { name: string }>(`/api/trips/${tripId}`, { name });
}

export async function deleteTripItem(tripId: string, day: number, itemId: string): Promise<Itinerary> {
  return apiDelete<Itinerary>(`/api/trips/${tripId}/days/${day}/items/${itemId}`);
}

export type UpdateTripItemPayload = {
  title?: string;
  timeSlot?: TimeSlot;
  durationMin?: number;
  stopType?: StopType;
  cost?: number;
  reason?: string;
};

export async function updateTripItem(
  tripId: string,
  day: number,
  itemId: string,
  payload: UpdateTripItemPayload,
): Promise<Itinerary> {
  return apiPatch<Itinerary, UpdateTripItemPayload>(`/api/trips/${tripId}/days/${day}/items/${itemId}`, payload);
}

/** 一次对话编辑的结果。changes 由后端依据实际执行成功的操作生成，不是模型写的。 */
export type ChatEditResult = {
  reply: string;
  changes: string[];
  changedItemIds: string[];
  itinerary: Itinerary | null;
  undoRemaining: number;
};

export type UndoResult = {
  remaining: number;
  itinerary: Itinerary | null;
};

export async function chatEditTrip(tripId: string, message: string): Promise<ChatEditResult> {
  return apiPost<ChatEditResult, { message: string }>(`/api/trips/${tripId}/chat`, { message });
}

export async function getUndoState(tripId: string): Promise<UndoResult> {
  return apiGet<UndoResult>(`/api/trips/${tripId}/undo`);
}

export async function undoTripEdit(tripId: string): Promise<UndoResult> {
  return apiPost<UndoResult>(`/api/trips/${tripId}/undo`);
}
