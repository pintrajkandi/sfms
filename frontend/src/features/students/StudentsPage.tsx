import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/api/client";
import type { Paginated, Student } from "@/api/types";
import { Card } from "@/components/Card";

export function StudentsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["students", search],
    queryFn: () =>
      api.get<Paginated<Student>>(
        `/students/${search ? `?search=${encodeURIComponent(search)}` : ""}`,
      ),
  });

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Students</h1>
          <p className="text-sm text-slate-500">Enrolled students</p>
        </div>
        <div className="flex items-center gap-3">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name, ID, guardian…"
            className="w-72 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <Link
            to="/students/new"
            className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark"
          >
            Add student
          </Link>
        </div>
      </header>

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[560px] text-sm">
          <thead className="border-b border-slate-100 text-left text-slate-500">
            <tr>
              <th className="px-6 py-3 font-medium">Student ID</th>
              <th className="px-6 py-3 font-medium">Name</th>
              <th className="px-6 py-3 font-medium">Grade</th>
              <th className="px-6 py-3 font-medium">Guardian</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data?.results.map((s) => (
              <tr
                key={s.id}
                onClick={() => navigate(`/students/${s.id}`)}
                className="cursor-pointer hover:bg-slate-50"
              >
                <td className="px-6 py-3 font-mono text-xs">{s.student_id}</td>
                <td className="px-6 py-3 font-medium text-slate-800">{s.full_name}</td>
                <td className="px-6 py-3">{s.grade || "—"}</td>
                <td className="px-6 py-3 text-slate-600">{s.guardian_name || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <p className="px-6 py-4 text-slate-500">Loading…</p>}
        {data?.results.length === 0 && (
          <p className="px-6 py-4 text-slate-400">No students found.</p>
        )}
      </Card>
    </div>
  );
}
