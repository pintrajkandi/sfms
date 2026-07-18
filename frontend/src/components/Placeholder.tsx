import { Card } from "./Card";

export function Placeholder({ title }: { title: string }) {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
      <Card>
        <p className="text-slate-500">
          This module is scaffolded. Build the {title.toLowerCase()} feature under{" "}
          <code className="rounded bg-slate-100 px-1">src/features</code>.
        </p>
      </Card>
    </div>
  );
}
