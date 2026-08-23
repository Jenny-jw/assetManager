export type OrderItem = {
  id: string;
  order_id: string;
  stock_id: string;
  stock_name: string;
  stock_available?: boolean;
  /** Number of packages ordered */
  quantity: number;
  /** Price per package at time of order */
  unit_price: number;
  line_total: number;
};

export type OrderStatus = "pending" | "confirmed" | "cancelled";

export type Order = {
  id: string;
  user_id: string;
  status: OrderStatus;
  total_amount: number;
  created_at: string;
  items: OrderItem[];
};

export type CreateOrderItem = {
  stock_id: string;
  quantity: number;
};

export type CreateOrderPayload = {
  items: CreateOrderItem[];
};