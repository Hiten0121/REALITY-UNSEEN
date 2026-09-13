import { supabase } from "./supabase.js";

export async function signUp({
  email,
  password,
  username,
  fullName
}) {
  const { data, error } =
    await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          username,
          full_name: fullName
        }
      }
    });

  if (error) {
    throw error;
  }

  return data;
}


export async function signIn({
  email,
  password
}) {
  const { data, error } =
    await supabase.auth.signInWithPassword({
      email,
      password
    });

  if (error) {
    throw error;
  }

  return data;
}


export async function signOut() {
  const { error } =
    await supabase.auth.signOut();

  if (error) {
    throw error;
  }
}


export async function getCurrentUser() {
  const { data, error } =
    await supabase.auth.getUser();

  if (error) {
    return null;
  }

  return data.user;
}


export function listenToAuthChanges(callback) {
  return supabase.auth.onAuthStateChange(
    (_event, session) => {
      callback(session?.user ?? null);
    }
  );
}