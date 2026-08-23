import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

/** Edge redirect so `/` never depends on `app/page.tsx` being in the Vercel route table. */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (pathname === "/" || pathname === "/index.html") {
    return NextResponse.redirect(new URL("/season/2025", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/index.html"],
};
