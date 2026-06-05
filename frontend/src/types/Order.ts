export type OrderItem = {
  id: string;
  order_id: string;
  tea_id: string;
  tea_name: string;
  /** Number of packages ordered */
  quantity: number;
  /** Price per package at time of order */
  unit_price: number;
  line_total: number;
};

export type Order = {
  id: string;
  user_id: string;
  status: "confirmed" | "cancelled";
  total_amount: number;
  created_at: string;
  items: OrderItem[];
};

export type CreateOrderItem = {
  tea_id: string;
  quantity: number;
};

export type CreateOrderPayload = {
  items: CreateOrderItem[];
};