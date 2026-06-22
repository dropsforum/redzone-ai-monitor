"use client";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white text-slate-800 antialiased">
        <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center gap-5 p-6 text-center font-sans">
          <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">
            DROPS Red Zone Monitor
          </div>
          <h1 className="text-2xl font-black tracking-tight text-slate-900">
            Something went wrong
          </h1>
          <p className="text-sm leading-6 text-slate-500">
            The monitor could not recover from an application error.
          </p>
          <button
            type="button"
            onClick={reset}
            className="h-11 rounded-lg border border-slate-200 px-5 text-[10px] font-black uppercase tracking-widest text-[#55799a] shadow-sm transition-colors hover:bg-slate-50"
          >
            Try Again
          </button>
        </main>
      </body>
    </html>
  );
}
