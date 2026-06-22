import { SiteShell } from "@/components/site-shell";
import { LoadingState } from "@/components/state-panels";

export default function Loading() {
  return (
    <SiteShell>
      <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        <LoadingState />
      </main>
    </SiteShell>
  );
}
