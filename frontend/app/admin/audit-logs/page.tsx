"use client";

import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { Pagination } from "@/components/ui/Pagination";
import { api, ApiClientError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { AuditLog, Paginated } from "@/lib/types";

export default function AdminAuditLogsPage() {
  return (
    <RequireAuth role="admin">
      <AdminAuditLogsContent />
    </RequireAuth>
  );
}

function AdminAuditLogsContent() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<Paginated<AuditLog>>("/api/v1/admin/audit-logs", {
          page,
          page_size: 15,
          action: action || undefined,
        });
        setLogs(data.items);
        setTotalPages(data.total_pages);
        setTotal(data.total);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Failed to load audit logs.");
      }
    }
    void load();
  }, [action, page]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-4xl">Audit logs</h1>
        <p className="mt-2 text-[var(--ink-soft)]">
          Operational trail for registrations, logins, orders, payments, and product changes.
        </p>
      </div>
      <input
        className="input max-w-md"
        placeholder="Filter by action (e.g. order.created)"
        value={action}
        onChange={(e) => {
          setPage(1);
          setAction(e.target.value);
        }}
      />
      {error && <p className="text-sm text-rose-700">{error}</p>}
      <div className="surface overflow-hidden rounded-2xl">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-[var(--line)] bg-[var(--paper)]">
            <tr>
              <th className="px-4 py-3">When</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Entity</th>
              <th className="px-4 py-3">Actor</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} className="border-b border-[var(--line)]">
                <td className="px-4 py-3 text-[var(--ink-soft)]">{formatDate(log.created_at)}</td>
                <td className="px-4 py-3 font-medium">{log.action}</td>
                <td className="px-4 py-3">
                  {log.entity_type}
                  {log.entity_id ? ` #${log.entity_id}` : ""}
                </td>
                <td className="px-4 py-3">{log.user_email || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
    </div>
  );
}
