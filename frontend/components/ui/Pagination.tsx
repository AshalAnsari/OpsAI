"use client";

type Props = {
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
};

export function Pagination({ page, totalPages, total, onPageChange }: Props) {
  if (totalPages <= 1) {
    return (
      <p className="text-sm text-[var(--ink-soft)]">
        Showing {total} item{total === 1 ? "" : "s"}
      </p>
    );
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-[var(--ink-soft)]">
        Page {page} of {totalPages} · {total} total
      </p>
      <div className="flex gap-2">
        <button
          className="btn btn-secondary"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </button>
        <button
          className="btn btn-secondary"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
