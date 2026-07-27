import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { content } from "@/api/resources";
import { formatDate } from "@/lib/dates";
import { MarketingLayout } from "./MarketingLayout";

export function BlogPostPage() {
  const { slug } = useParams();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["blog-post", slug],
    queryFn: () => content.post(slug!),
    enabled: Boolean(slug),
    retry: false,
  });

  return (
    <MarketingLayout>
      <article className="mx-auto max-w-3xl px-6 py-16">
        <Link to="/blog" className="text-sm font-medium text-indigo-600 hover:underline">← Back to blog</Link>

        {isLoading && <p className="mt-8 text-slate-400">Loading…</p>}
        {isError && <p className="mt-8 text-slate-400">This post could not be found.</p>}

        {data && (
          <>
            <p className="mt-6 text-xs text-slate-400">
              {data.published_at ? formatDate(data.published_at) : ""}{data.author ? ` · ${data.author}` : ""}
            </p>
            <h1 className="mt-2 text-4xl font-extrabold leading-tight text-slate-900">{data.title}</h1>
            {data.excerpt && <p className="mt-4 text-lg text-slate-500">{data.excerpt}</p>}
            {data.cover_image && <img src={data.cover_image} alt="" className="mt-8 w-full rounded-2xl object-cover" />}

            <div className="mt-8 space-y-4 text-base leading-relaxed text-slate-700">
              {data.body.split(/\n{2,}/).map((para, i) => (
                <p key={i} className="whitespace-pre-line">{para}</p>
              ))}
            </div>
          </>
        )}
      </article>
    </MarketingLayout>
  );
}
