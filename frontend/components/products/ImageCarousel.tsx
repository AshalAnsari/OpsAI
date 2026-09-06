"use client";

import { useEffect, useState } from "react";

type Props = {
  images: string[];
  alt: string;
};

export function ImageCarousel({ images, alt }: Props) {
  const slides = images.length > 0 ? images : [];
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setIndex(0);
  }, [images]);

  if (slides.length === 0) {
    return (
      <div className="flex aspect-[4/3] items-center justify-center rounded-2xl bg-[var(--paper-deep)] text-sm text-[var(--ink-soft)]">
        No product images yet
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-2xl bg-[var(--paper-deep)]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={slides[index]}
          alt={`${alt} ${index + 1}`}
          className="aspect-[4/3] w-full object-cover"
        />
        {slides.length > 1 && (
          <>
            <button
              type="button"
              className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-white/90 px-3 py-2 text-sm shadow"
              onClick={() => setIndex((i) => (i - 1 + slides.length) % slides.length)}
            >
              Prev
            </button>
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-white/90 px-3 py-2 text-sm shadow"
              onClick={() => setIndex((i) => (i + 1) % slides.length)}
            >
              Next
            </button>
          </>
        )}
      </div>
      {slides.length > 1 && (
        <div className="flex gap-2 overflow-x-auto">
          {slides.map((url, i) => (
            <button
              key={`${url}-${i}`}
              type="button"
              className={`h-16 w-16 shrink-0 overflow-hidden rounded-lg border ${
                i === index ? "border-[var(--accent)]" : "border-[var(--line)]"
              }`}
              onClick={() => setIndex(i)}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={url} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
