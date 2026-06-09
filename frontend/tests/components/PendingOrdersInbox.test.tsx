import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PendingOrdersInbox from "@/components/PendingOrdersInbox";
import type { Order } from "@/types/Order";

const { listOrdersMock, approveOrderMock, rejectOrderMock } = vi.hoisted(() => ({
  listOrdersMock: vi.fn(),
  approveOrderMock: vi.fn(),
  rejectOrderMock: vi.fn(),
}));

vi.mock("@/services/orderServices", () => ({
  listOrders: listOrdersMock,
  approveOrder: approveOrderMock,
  rejectOrder: rejectOrderMock,
}));

const availableOrder: Order = {
  id: "order-1",
  user_id: "user-1",
  status: "pending",
  total_amount: 300,
  created_at: "2026-01-01T00:00:00Z",
  items: [
    {
      id: "item-1",
      order_id: "order-1",
      tea_id: "tea-1",
      tea_name: "Fresh Oolong",
      tea_available: true,
      quantity: 1,
      unit_price: 300,
      line_total: 300,
    },
  ],
};

const unavailableOrder: Order = {
  ...availableOrder,
  id: "order-2",
  items: [
    {
      ...availableOrder.items[0],
      id: "item-2",
      order_id: "order-2",
      tea_name: "Deleted Tea",
      tea_available: false,
    },
  ],
};

describe("PendingOrdersInbox", () => {
  beforeEach(() => {
    listOrdersMock.mockReset();
    approveOrderMock.mockReset();
    rejectOrderMock.mockReset();
    vi.stubGlobal("confirm", vi.fn(() => true));
  });

  it("shows approve and reject for available teas", async () => {
    listOrdersMock.mockResolvedValue([availableOrder]);
    render(<PendingOrdersInbox />);

    expect(await screen.findByText("Fresh Oolong ×1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
  });

  it("shows remove for orders with deleted tea", async () => {
    listOrdersMock.mockResolvedValue([unavailableOrder]);
    render(<PendingOrdersInbox />);

    expect(
      await screen.findByText("Deleted Tea (no longer available) ×1"),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Remove" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
  });

  it("removes unavailable orders via reject API", async () => {
    listOrdersMock
      .mockResolvedValueOnce([unavailableOrder])
      .mockResolvedValueOnce([]);
    rejectOrderMock.mockResolvedValue({ ...unavailableOrder, status: "cancelled" });

    render(<PendingOrdersInbox />);
    fireEvent.click(await screen.findByRole("button", { name: "Remove" }));

    await waitFor(() => {
      expect(rejectOrderMock).toHaveBeenCalledWith("order-2");
    });
  });
});
