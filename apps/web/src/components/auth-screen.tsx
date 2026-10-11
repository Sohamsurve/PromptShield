import Link from "next/link";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

export const authFieldClass =
  "w-full rounded-panel border-2 border-ink bg-background px-3 text-sm text-foreground outline-none focus:border-uv";

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
    <div className="mx-auto flex w-full max-w-md flex-col justify-center px-4 py-10">
      <Card>
        <CardHeader className="gap-2">
          <CardTitle className="text-2xl leading-none">
            <h1>{title}</h1>
          </CardTitle>
          <CardDescription>{detail}</CardDescription>
        </CardHeader>
        {children}
        <p className="px-6 pb-6 text-center text-sm leading-none text-muted-foreground">{footer}</p>
      </Card>
    </div>
  );
}

export function AuthFields({ children }: { children: React.ReactNode }) {
  return <CardContent className="grid gap-4">{children}</CardContent>;
}

export function AuthLabel({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium leading-none">
      {children}
    </label>
  );
}

export function AuthFooter({ children }: { children: React.ReactNode }) {
  return <CardFooter className="flex-col items-stretch gap-3">{children}</CardFooter>;
}

export function AuthLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="font-medium text-foreground underline underline-offset-4">
      {children}
    </Link>
  );
}
