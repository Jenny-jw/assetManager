import api from "../lib/axios";
import type { CreateOrderPayload, Order, OrderStatus } from "../types/Order";

export const createOrder = async (payload: CreateOrderPayload): Promise<Order> => {
  const response = await api.post<Order>("/orders/", payload);
  return response.data;
};

export const listOrders = async (status?: OrderStatus): Promise<Order[]> => {
  const response = await api.get<{ data: Order[]; total: number }>("/orders/", {
    params: status ? { status, limit: 50 } : undefined,
  });
  return response.data.data;
};

export const approveOrder = async (orderId: string): Promise<Order> => {
  const response = await api.patch<Order>(`/orders/${orderId}/approve`);
  return response.data;
};

export const rejectOrder = async (orderId: string): Promise<Order> => {
  const response = await api.patch<Order>(`/orders/${orderId}/reject`);
  return response.data;
};
