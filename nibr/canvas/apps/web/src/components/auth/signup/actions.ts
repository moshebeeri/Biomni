"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";

import { signUp } from "@/lib/auth/server";
import { SignupWithEmailInput } from "./Signup";

export async function signup(input: SignupWithEmailInput, baseUrl: string) {
  console.log('Signup attempt for:', input.email);

  try {
    const result = await signUp(input.email, input.password);
    
    if (result.success) {
      console.log('Signup successful for:', input.email);
      revalidatePath("/", "layout");
      // In development, we auto-login after signup, so redirect to main page
      redirect("/");
    } else {
      console.error('Signup failed:', result.error);
      redirect("/auth/signup?error=true");
    }
  } catch (error) {
    console.error('Signup error:', error);
    redirect("/auth/signup?error=true");
  }
}
