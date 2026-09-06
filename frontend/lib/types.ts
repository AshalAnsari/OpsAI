export type Role = "admin" | "customer";

export type AuthUser = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  roles: Role[];
};

export type Product = {
  id: number;
  name: string;
  slug: string;
  description: string;
  price: string | number;
  stock_quantity: number;
  is_active: boolean;
  image_urls: string[];
  specs: Record<string, string>;
  created_at: string;
  updated_at: string;
};

export type OrderStatus =
  | "pending"
  | "confirmed"
  | "processing"
  | "dispatched"
  | "in_transit_international"
  | "customs_clearance"
  | "out_for_delivery"
  | "delivered"
  | "cancelled";

export type PaymentStatus = "unpaid" | "pending" | "paid" | "failed" | "refunded";

export type OrderItem = {
  id: number;
  product_id: number;
  product_name?: string | null;
  quantity: number;
  unit_price: string | number;
  subtotal: string | number;
};

export type Order = {
  id: number;
  display_id: string;
  customer_id: number;
  status: OrderStatus;
  payment_status: PaymentStatus;
  total_amount: string | number;
  shipping_country: string;
  shipping_country_name?: string | null;
  current_location?: string | null;
  status_changed_at?: string | null;
  stripe_checkout_session_id?: string | null;
  checkout_url?: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
  customer_email?: string | null;
  customer_name?: string | null;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type DashboardMetrics = {
  total_customers: number;
  total_orders: number;
  pending_orders: number;
  processing_orders: number;
  delivered_orders: number;
  cancelled_orders: number;
  total_revenue: string | number;
  recent_orders: Order[];
  recent_customers: AdminCustomer[];
  recent_audit_logs: AuditLog[];
};

export type AdminCustomer = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  created_at: string;
  order_count: number;
  total_spent: number;
};

export type AuditLog = {
  id: number;
  user_id: number | null;
  user_email?: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
};

export type SupportTicket = {
  id: number;
  display_id: string;
  customer_id: number;
  customer_email?: string | null;
  customer_name?: string | null;
  subject: string;
  status: "open" | "in_progress" | "resolved" | "closed";
  created_at: string;
  updated_at: string;
  messages: SupportMessage[];
};

export type SupportMessage = {
  id: number;
  ticket_id: number;
  sender_id: number;
  sender_name?: string | null;
  body: string;
  is_staff: boolean;
  created_at: string;
};

export type AppNotification = {
  id: number;
  title: string;
  body: string;
  link?: string | null;
  is_read: boolean;
  created_at: string;
  expires_at: string;
};

export type ApiError = {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
};

export type CartItem = {
  product: Product;
  quantity: number;
};

export type FulfillmentAdvanceResult = {
  advanced_count: number;
  run_date: string;
  triggered_by: string;
  skipped: boolean;
  message: string;
};
