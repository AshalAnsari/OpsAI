import type { OrderStatus } from "@/lib/types";

export function formatMoney(value: string | number): string {
  const amount = typeof value === "string" ? Number(value) : value;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number.isFinite(amount) ? amount : 0);
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatShippingAddress(order: {
  shipping_address_line1?: string | null;
  shipping_address_line2?: string | null;
  shipping_city?: string | null;
  shipping_state?: string | null;
  shipping_postal_code?: string | null;
  shipping_country?: string | null;
  shipping_country_name?: string | null;
}): string {
  const lines: string[] = [];
  if (order.shipping_address_line1) lines.push(order.shipping_address_line1);
  if (order.shipping_address_line2) lines.push(order.shipping_address_line2);

  const cityLine = [order.shipping_city, order.shipping_state, order.shipping_postal_code]
    .filter(Boolean)
    .join(", ");
  if (cityLine) lines.push(cityLine);

  const country = order.shipping_country_name || order.shipping_country;
  if (country) {
    lines.push(
      order.shipping_country && order.shipping_country_name
        ? `${order.shipping_country_name} (${order.shipping_country})`
        : country,
    );
  }
  return lines.join("\n") || "—";
}

export function formatStatusLabel(status: string): string {
  return status.replaceAll("_", " ");
}

export function statusColor(status: string): string {
  switch (status) {
    case "pending":
      return "background:#fef3c7;color:#92400e";
    case "confirmed":
      return "background:#dbeafe;color:#1e40af";
    case "processing":
      return "background:#e0e7ff;color:#3730a3";
    case "dispatched":
    case "shipped":
      return "background:#ccfbf1;color:#0f766e";
    case "in_transit_international":
      return "background:#cffafe;color:#155e75";
    case "customs_clearance":
      return "background:#fef9c3;color:#854d0e";
    case "out_for_delivery":
      return "background:#fce7f3;color:#9d174d";
    case "delivered":
      return "background:#dcfce7;color:#166534";
    case "cancelled":
      return "background:#fee2e2;color:#991b1b";
    case "paid":
      return "background:#dcfce7;color:#166534";
    default:
      return "background:#f3f4f6;color:#374151";
  }
}

export const DOMESTIC_ORDER_FLOW = [
  "pending",
  "confirmed",
  "processing",
  "dispatched",
  "out_for_delivery",
  "delivered",
] as const;

export const INTERNATIONAL_ORDER_FLOW = [
  "pending",
  "confirmed",
  "processing",
  "dispatched",
  "in_transit_international",
  "customs_clearance",
  "out_for_delivery",
  "delivered",
] as const;

/** @deprecated Prefer orderFlowForCountry */
export const ORDER_FLOW = DOMESTIC_ORDER_FLOW;

export function orderFlowForCountry(shippingCountry?: string | null): readonly OrderStatus[] {
  return (shippingCountry || "US").toUpperCase() === "US"
    ? DOMESTIC_ORDER_FLOW
    : INTERNATIONAL_ORDER_FLOW;
}

export const ALL_ORDER_STATUSES: OrderStatus[] = [
  "pending",
  "confirmed",
  "processing",
  "dispatched",
  "in_transit_international",
  "customs_clearance",
  "out_for_delivery",
  "delivered",
  "cancelled",
];

export const SHIPPING_COUNTRIES = [
  { code: "US", name: "United States" },
  { code: "CA", name: "Canada" },
  { code: "GB", name: "United Kingdom" },
  { code: "DE", name: "Germany" },
  { code: "FR", name: "France" },
  { code: "AU", name: "Australia" },
  { code: "JP", name: "Japan" },
  { code: "IN", name: "India" },
  { code: "BR", name: "Brazil" },
  { code: "MX", name: "Mexico" },
] as const;
