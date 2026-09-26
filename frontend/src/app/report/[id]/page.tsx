"use client";

import { use, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ReportRedirectPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = use(params);

  useEffect(() => {
    if (id) {
      router.replace(`/?session_id=${id}`);
    }
  }, [id, router]);

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-xs text-slate-400">
      Loading Report Session {id}...
    </div>
  );
}
