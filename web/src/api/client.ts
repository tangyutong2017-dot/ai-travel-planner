export class ApiError extends Error {
  status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

async function throwApiError(response: Response): Promise<never> {
  let message = `请求失败：${response.status}`

  try {
    const data = await response.json() as { detail?: unknown; message?: unknown }
    const detail = data.detail ?? data.message
    if (typeof detail === 'string' && detail.trim()) {
      message = detail
    } else if (Array.isArray(detail) && detail.length > 0) {
      message = detail.map((item) => typeof item === 'object' && item !== null && 'msg' in item ? String(item.msg) : String(item)).join('；')
    }
  } catch {
    // Keep the HTTP status fallback when the response body is not JSON.
  }

  throw new ApiError(message, response.status)
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`)

  if (!response.ok) {
    await throwApiError(response)
  }

  return response.json() as Promise<T>
}

export async function apiPost<TResponse, TPayload = unknown>(path: string, payload?: TPayload): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: payload === undefined ? undefined : JSON.stringify(payload),
  })

  if (!response.ok) {
    await throwApiError(response)
  }

  return response.json() as Promise<TResponse>
}

export async function apiDelete<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    await throwApiError(response)
  }

  return response.json() as Promise<TResponse>
}

export async function apiPatch<TResponse, TPayload = unknown>(path: string, payload: TPayload): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    await throwApiError(response)
  }

  return response.json() as Promise<TResponse>
}
