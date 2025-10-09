import NextAuth, { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          // Call backend login API
          const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
          const response = await fetch(`${backendUrl}/auth/login`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!response.ok) {
            return null;
          }

          const data = await response.json();

          // Return user object with all necessary fields
          return {
            id: data.user.id.toString(),
            email: data.user.email,
            name: data.user.display_name,
            access_token: data.access_token,
            roles: data.user.roles,
            org_ids: data.user.org_ids,
            project_ids: data.user.project_ids,
            home: data.home,
          };
        } catch (error) {
          console.error("Auth error:", error);
          return null;
        }
      },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, user }) {
      // Initial sign in
      if (user) {
        token.access_token = user.access_token;
        token.roles = user.roles;
        token.org_ids = user.org_ids;
        token.project_ids = user.project_ids;
        token.home = user.home;
      }
      return token;
    },
    async session({ session, token }) {
      // Expose fields to client
      if (token) {
        session.access_token = token.access_token as string;
        session.user.roles = token.roles as string[];
        session.user.org_ids = token.org_ids as number[];
        session.user.project_ids = token.project_ids as number[];
        session.home = token.home as string;
      }
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };


