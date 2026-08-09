import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Order } from "../types/Order";
import { approveOrder, listOrders, rejectOrder } from "../services/orderServices";

type Props = {
  refreshToken?: number;
  onPendingCountChange?: (count: number) => void;
  onInventoryChange?: () => void;
};

function orderHasUnavailableTea(order: Order): boolean {
  return order.items.some((item) => item.tea_available === false);
}

const PendingOrdersInbox = ({
  refreshToken = 0,
  onPendingCountChange,
  onInventoryChange,
}: Props) => {
  const { t } = useTranslation();
  const [orders, setOrders] = useState<Order[]>([]);
  const [actingId, setActingId] = useState<string | null>(null);

  const formatItemLabel = (
    teaName: string,
    quantity: number,
    teaAvailable: boolean,
  ): string => {
    const label = teaAvailable
      ? teaName
      : t("widgets.itemUnavailable", { name: teaName });
    return `${label} ×${quantity}`;
  };

  const refreshPendingOrders = async () => {
    const data = await listOrders("pending");
    setOrders(data);
    onPendingCountChange?.(data.length);
  };

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
      await refreshPendingOrders();
    } catch {
      alert(t("widgets.approveFailed"));
    } finally {
      setActingId(null);
    }
  };

  const handleReject = async (orderId: string) => {
    const confirmed = window.confirm(t("widgets.rejectConfirm"));
    if (!confirmed) return;

    setActingId(orderId);
    try {
      await rejectOrder(orderId);
      await refreshPendingOrders();
    } catch {
      alert(t("widgets.rejectFailed"));
    } finally {
      setActingId(null);
    }
  };

  const handleRemove = async (orderId: string) => {
    setActingId(orderId);
    try {
      await rejectOrder(orderId);
      await refreshPendingOrders();
    } catch {
      alert(t("widgets.removeFailed"));
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500 h-full">
      <h2 className="font-semibold mb-3">{t("widgets.pendingOrders")}</h2>

      {orders.length === 0 ? (
        <p className="text-sm text-gray-400 py-4 text-center">
          {t("widgets.noPendingOrders")}
        </p>
      ) : (
        <ul className="space-y-3 max-h-64 overflow-y-auto">
          {orders.map((order) => {
            const summary = order.items
              .map((item) =>
                formatItemLabel(
                  item.tea_name,
                  item.quantity,
                  item.tea_available !== false,
                ),
              )
              .join(", ");
            const isActing = actingId === order.id;
            const hasUnavailableTea = orderHasUnavailableTea(order);

            return (
              <li
                key={order.id}
                className="border-b border-gray-200 pb-3 last:border-b-0"
              >
                <p className="text-sm font-medium text-gray-600 truncate">
                  {summary}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {t("widgets.orderTotal", {
                    amount: order.total_amount.toLocaleString(),
                  })}
                </p>
                {hasUnavailableTea ? (
                  <div className="flex justify-end mt-2">
                    <button
                      type="button"
                      onClick={() => void handleRemove(order.id)}
                      disabled={isActing}
                      className="w-1/2 px-2 py-1 text-xs rounded-lg bg-[#894f45] text-white hover:bg-red-700 transition disabled:opacity-60"
                    >
                      {isActing ? t("widgets.acting") : t("widgets.remove")}
                    </button>
                  </div>
                ) : (
                  <div className="flex gap-2 mt-2">
                    <button
                      type="button"
                      onClick={() => void handleApprove(order.id)}
                      disabled={isActing}
                      className="flex-1 px-2 py-1 text-xs rounded-lg bg-[#78a043] text-white hover:bg-lime-900 transition disabled:opacity-60"
                    >
                      {isActing ? t("widgets.acting") : t("widgets.approve")}
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleReject(order.id)}
                      disabled={isActing}
                      className="flex-1 px-2 py-1 text-xs rounded-lg bg-[#894f45] text-white hover:bg-red-700 transition disabled:opacity-60"
                    >
                      {t("widgets.reject")}
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default PendingOrdersInbox;
