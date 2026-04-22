import axiosClient from "./axiosClient";
import type { AuthResponse } from "../types";

export interface AuthRequest {
  email: string;
  password: string;
}

export async function registerUser(payload: AuthRequest): Promise<AuthResponse> {
  const response = await axiosClient.post("/auth/register", payload);
  return response.data;
}

export async function loginUser(payload: AuthRequest): Promise<AuthResponse> {
  const response = await axiosClient.post("/auth/login", payload);
  return response.data;
}
