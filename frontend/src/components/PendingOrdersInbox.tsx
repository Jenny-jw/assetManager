import { useEffect, useState } from "react";
import type { Order } from "../types/Order";
import { approveOrder, listOrders, rejectOrder } from "../services/orderServices";

type Props = {
  refreshToken?: number;
  onPendingCountChange?: (count: number) => void;
  onInventoryChange?: () => void;
};

const PendingOrdersInbox = ({
  refreshToken = 0,
  onPendingCountChange,
  onInventoryChange,
}: Props) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [actingId, setActingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    listOrders("pending")
      .then((data) => {
        if (cancelled) return;
        setOrders(data);
        onPendingCountChange?.(data.length);
      })
      .catch((error) => {
        console.error("Failed to load pending orders:", error);
      });

    return () => {
      cancelled = true;
    };
  }, [refreshToken, onPendingCountChange]);

  const handleApprove = async (orderId: string) => {
    setActingId(orderId);
    try {
      await approveOrder(orderId);
      onInventoryChange?.();
      const data = await listOrders("pending");
      setOrders(data);
      onPendingCountChange?.(data.length);
    } catch {
      alert("Failed to approve order. Please try again.");
    } finally {
      setActingId(null);
    }
  };

  const handleReject = async (orderId: string) => {
    const confirmed = window.confirm("Reject this order?");
    if (!confirmed) return;

    setActingId(orderId);
    try {
      await rejectOrder(orderId);
      const data = await listOrders("pending");
      setOrders(data);
      onPendingCountChange?.(data.length);
    } catch {
      alert("Failed to reject order. Please try again.");
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500 h-full">
      <h2 className="font-semibold mb-3">Pending Orders</h2>

      {orders.length === 0 ? (
        <p className="text-sm text-gray-400 py-4 text-center">
          No pending orders at the moment
        </p>
      ) : (
        <ul className="space-y-3 max-h-64 overflow-y-auto">
          {orders.map((order) => {
            const summary = order.items
              .map((item) => `${item.tea_name} ×${item.quantity}`)
              .join(", ");
            const isActing = actingId === order.id;

            return (
              <li
                key={order.id}
                className="border-b border-gray-200 pb-3 last:border-b-0"
              >
                <p className="text-sm font-medium text-gray-600 truncate">
                  {summary}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  Total: {order.total_amount.toLocaleString()}
                </p>
                <div className="flex gap-2 mt-2">
                  <button
                    type="button"
                    onClick={() => void handleApprove(order.id)}
                    disabled={isActing}
                    className="flex-1 px-2 py-1 text-xs rounded-lg bg-[#78a043] text-white hover:bg-lime-900 transition disabled:opacity-60"
                  >
                    {isActing ? "…" : "Approve"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleReject(order.id)}
                    disabled={isActing}
                    className="flex-1 px-2 py-1 text-xs rounded-lg bg-[#894f45] text-white hover:bg-red-700 transition disabled:opacity-60"
                  >
                    Reject
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default PendingOrdersInbox;
