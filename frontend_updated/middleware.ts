import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token;
    const path = req.nextUrl.pathname;

    // If no token, redirect to login
    if (!token) {
      return NextResponse.redirect(new URL("/login", req.url));
    }

    const roles = (token.roles as string[]) || [];

    // Route guards based on roles
    if (path.startsWith("/console/system")) {
      if (!roles.includes("SYSTEM_ADMIN")) {
        return NextResponse.redirect(new URL("/login", req.url));
      }
    } else if (path.startsWith("/console/org")) {
      if (!roles.includes("ORG_ADMIN")) {
        return NextResponse.redirect(new URL("/login", req.url));
      }
    } else if (path.startsWith("/console/project")) {
      if (!roles.includes("PM")) {
        return NextResponse.redirect(new URL("/login", req.url));
      }
    } else if (path.startsWith("/annotator")) {
      if (!roles.includes("ANNOTATOR")) {
        return NextResponse.redirect(new URL("/login", req.url));
      }
    } else if (path.startsWith("/qa")) {
      if (!roles.includes("QA")) {
        return NextResponse.redirect(new URL("/login", req.url));
      }
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => !!token,
    },
  }
);

// Protect all routes except static assets and login
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     * - login page
     * - api/auth (NextAuth routes)
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$|api/auth|login).*)",
  ],
};


