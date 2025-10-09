import "next-auth";
import { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    access_token: string;
    home: string;
    user: {
      roles: string[];
      org_ids: number[];
      project_ids: number[];
    } & DefaultSession["user"];
  }

  interface User {
    access_token: string;
    roles: string[];
    org_ids: number[];
    project_ids: number[];
    home: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    access_token: string;
    roles: string[];
    org_ids: number[];
    project_ids: number[];
    home: string;
  }
}


