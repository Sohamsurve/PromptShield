import Link from "next/link";

const panel = "rounded-panel border-2 border-ink bg-surface shadow-[4px_4px_0_0_var(--ink)]";

export const authFieldClass =
  "w-full rounded-panel border-2 border-ink bg-paper px-3 text-sm text-ink outline-none focus:border-uv";

export function AuthScreen({
  title,
  detail,
  children,
  footer,
}: {
  title: string;
  detail: string;
  children: React.ReactNode;
  footer: React.ReactNode;
}) {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col px-4 py-14 md:px-8 md:py-20">
      <div className="mx-auto flex w-full max-w-md flex-col gap-6">
        <div className="flex flex-col gap-3">
          <p className="font-mono text-xs text-uv">Account</p>
          <h1 className="text-4xl font-bold tracking-tight text-ink">{title}</h1>
          <p className="text-sm leading-relaxed text-slate md:text-base">{detail}</p>
        </div>
        <div className={panel}>
          {children}
          <p className="px-6 pb-6 text-sm leading-relaxed text-slate">{footer}</p>
        </div>
      </div>
    </div>
  );
}

export function AuthFields({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-col gap-4 p-6">{children}</div>;
}

export function AuthLabel({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium leading-none text-ink">
      {children}
    </label>
  );
}

export function AuthFooter({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-col items-stretch gap-3 px-6 pb-2">{children}</div>;
}

export function AuthLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="font-medium text-ink underline decoration-uv underline-offset-4">
      {children}
    </Link>
  );
}
