"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { signIn } from "@/lib/auth/server";
import { LoginWithEmailInput } from "./Login";

export async function login(input: LoginWithEmailInput) {
  console.log('Login attempt for:', input.email);

  try {
    const result = await signIn(input.email, input.password);
    
    if (result.success) {
      console.log('Login successful for:', input.email);
      revalidatePath("/", "layout");
      redirect("/");
    } else {
      console.error('Login failed:', result.error);
      redirect("/auth/login?error=true");
    }
  } catch (error) {
    console.error('Login error:', error);
    redirect("/auth/login?error=true");
  }
}
