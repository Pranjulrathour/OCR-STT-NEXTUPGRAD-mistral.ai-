export interface ApiSuccess<T> {
  success: true;
  data?: T;
  message: string;
}

export interface ApiFailure {
  success: false;
  message: string;
}

export type ApiResponse<T> = (ApiSuccess<T> & T) | ApiFailure;

export interface HealthStatus {
  status: "healthy" | "degraded";
  version: string;
}
