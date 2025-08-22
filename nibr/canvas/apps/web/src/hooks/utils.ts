import { Client } from "@/lib/langchain-compat";

export const createClient = () => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:54367";
  return new Client({ apiUrl });
};
