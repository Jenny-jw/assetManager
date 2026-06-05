import api from "../lib/axios";
import type { CreateOrderPayload, Order } from "../types/Order";

export const createOrder = async (payload: CreateOrderPayload): Promise<Order> => {
  const response = await api.post<Order>("/orders/", payload);
  return response.data;
};

export const listOrders = async (): Promise<Order[]> => {
  const response = await api.get<{ data: Order[]; total: number }>("/orders/");
  return response.data.data;
};