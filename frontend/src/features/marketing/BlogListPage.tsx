import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { content } from "@/api/resources";
import { formatDate } from "@/lib/dates";
import { MarketingLayout } from "./MarketingLayout";

export function BlogListPage() {
  const { data, isLoading } = useQuery({ queryKey: ["blog-posts"], queryFn: () => content.posts() });
  const posts = data ?? [];

  return (
    <MarketingLayout>
      <section className="mx-auto max-w-5xl px-6 py-16">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">Blog</p>
        <h1 className="mt-3 text-4xl font-extrabold text-slate-900">News &amp; insights</h1>
        <p className="mt-3 max-w-xl text-lg text-slate-500">Product updates, guides and best practices for running school finances.</p>

        {isLoading && <p className="mt-10 text-slate-400">Loading…</p>}
        {!isLoading && posts.length === 0 && <p className="mt-10 text-slate-400">No posts yet — check back soon.</p>}

        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {posts.map((p) => (
            <Link key={p.id} to={`/blog/${p.slug}`} className="group flex flex-col overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
              {p.cover_image ? (
                <img src={p.cover_image} alt="" className="h-44 w-full object-cover" />
              ) : (
                <div className="flex h-44 w-full items-center justify-center bg-gradient-to-br from-indigo-500 to-violet-600 text-3xl text-white">📰</div>
              )}
              <div className="flex flex-1 flex-col p-5">
                <p className="text-xs text-slate-400">{p.published_at ? formatDate(p.published_at) : ""}{p.author ? ` · ${p.author}` : ""}</p>
                <h2 className="mt-1 text-lg font-bold text-slate-900 group-hover:text-indigo-600">{p.title}</h2>
                <p className="mt-2 line-clamp-3 flex-1 text-sm text-slate-500">{p.excerpt}</p>
                <span className="mt-4 text-sm font-semibold text-indigo-600">Read more →</span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </MarketingLayout>
  );
}
