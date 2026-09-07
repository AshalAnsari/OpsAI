"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { ApiClientError } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

const schema = z.object({
  first_name: z.string().trim().min(1, "First name is required"),
  last_name: z.string().trim().min(1, "Last name is required"),
  email: z.string().email("Enter a valid email"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Za-z]/, "Password must include a letter")
    .regex(/\d/, "Password must include a number"),
});

type FormValues = z.infer<typeof schema>;

export default function RegisterPage() {
  const { register: registerUser } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    setError(null);
    try {
      await registerUser(values);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to register.");
    }
  });

  return (
    <div className="mx-auto max-w-md">
      <h1 className="font-display text-4xl">Create account</h1>
      <p className="mt-2 text-[var(--ink-soft)]">Join Harbor Dock Station as a customer and place demo orders.</p>
      <form onSubmit={onSubmit} className="surface mt-6 space-y-4 rounded-2xl p-6">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">First name</label>
            <input className="input" {...register("first_name")} />
            {errors.first_name && <p className="mt-1 text-sm text-rose-700">{errors.first_name.message}</p>}
          </div>
          <div>
            <label className="label">Last name</label>
            <input className="input" {...register("last_name")} />
            {errors.last_name && <p className="mt-1 text-sm text-rose-700">{errors.last_name.message}</p>}
          </div>
        </div>
        <div>
          <label className="label">Email</label>
          <input className="input" type="email" {...register("email")} />
          {errors.email && <p className="mt-1 text-sm text-rose-700">{errors.email.message}</p>}
        </div>
        <div>
          <label className="label">Password</label>
          <input className="input" type="password" {...register("password")} />
          {errors.password && <p className="mt-1 text-sm text-rose-700">{errors.password.message}</p>}
        </div>
        {error && <p className="text-sm text-rose-700">{error}</p>}
        <button className="btn btn-primary w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating…" : "Create account"}
        </button>
      </form>
      <p className="mt-4 text-sm text-[var(--ink-soft)]">
        Already registered? <Link href="/login" className="text-[var(--accent)]">Sign in</Link>
      </p>
    </div>
  );
}
